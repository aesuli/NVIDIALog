import argparse
import sys
from datetime import timedelta, datetime

import numpy as np
import pandas as pd

# Converts a given number of seconds into a human-readable format based on a specified resolution.
def human_time(seconds, resolution='m'):
    td = timedelta(seconds=seconds)
    years = td.days // 365
    months = (td.days % 365) // 30
    days = (td.days % 365) % 30
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    seconds = (td.seconds % 3600) % 60

    if years > 0:
        output = f'{years}y '
    else:
        output = ''
    if resolution == 'y':
        return output
    if months > 0 or len(output) > 0:
        output += f'{months:2}M '
    else:
        output += ''
    if resolution == 'M':
        return output
    if days > 0 or len(output) > 0:
        output += f'{days:2}d '
    else:
        output += ''
    if resolution == 'd':
        return output
    if hours > 0 or len(output) > 0:
        output += f'{hours:2}h '
    else:
        output += ''
    if resolution == 'h':
        return output
    if minutes > 0 or len(output) > 0:
        output += f'{minutes:2}m '
    else:
        output += ''
    if resolution == 'm':
        return output
    if seconds > 0 or len(output) > 0:
        output += f'{seconds:2}s'
    else:
        output += ''

    return output

# Generates a report about GPU utilization and saves it to the specified output file.
def report(df, num_gpus, output_file, sort_by_use):
    if len(df) == 0:
        print("No data to process")
        return

    # Determine the time range of the data.
    start_time = df['epoch'].min()
    end_time = df['epoch'].max()
    end_time += df[df['epoch'] == end_time].interval.mean()
    timespan = int(end_time - start_time)

    # Infer the number of GPUs if not provided.
    if num_gpus == 0:
        num_gpus = int(df['gpu_id'].nunique())

    # Write basic report details to the output file.
    print(
        f'# Report ({datetime.fromtimestamp(end_time).strftime("%Y-%m-%d %H:%M")} - {datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M")})',
        file=output_file)
    print(f'Duration: {human_time(timespan)}', file=output_file)
    print(file=output_file)
    print(f'Number of GPUs: {num_gpus}', file=output_file)
    print(file=output_file)
    print(f'Total available compute time: {human_time(timespan * num_gpus)}', file=output_file)
    print(file=output_file)

    # Generate user-GPU utilization table.
    print('## User-GPU time', file=output_file)
    pt = df.pivot_table('interval', ['user', 'gpu_id'], aggfunc='sum')
    pt['% use'] = (pt['interval'] / timespan).apply(lambda x: f'{x:.1%}')
    if sort_by_use:
        pt = pt.sort_values('interval', ascending=False)
    pt['interval'] = pt['interval'].apply(human_time)
    print(pt.reset_index()
          .rename(columns={'idx1': '', 'idx2': ''}).to_markdown(index=False,
                                                                colalign=('left', 'left', 'right', 'right')),
          file=output_file)
    print(file=output_file)

    # Generate a table showing the number of processes per user.
    print('## Users, number of processes', file=output_file)
    gb = df.rename(columns={'pid': 'num processes'}).groupby('user')['num processes'].nunique()
    if sort_by_use:
        gb = gb.sort_values(ascending=False).reset_index()
    print(gb.to_markdown(),
          file=output_file)
    print(file=output_file)

    # Generate a table showing total compute time per user.
    print('## Users, total compute time', file=output_file)
    pt = df.drop_duplicates(subset=['epoch', 'user', 'gpu_id'], keep='last').pivot_table('interval', 'user',
                                                                                         aggfunc='sum')
    pt['% use'] = (pt['interval'] / (timespan * num_gpus)).apply(lambda x: f'{x:.1%}')
    if sort_by_use:
        pt = pt.sort_values('interval', ascending=False).reset_index()
    pt['interval'] = pt['interval'].apply(human_time)
    print(pt.to_markdown(colalign=('left', 'right', 'right')), file=output_file)
    print(file=output_file)

    # Generate a table showing total compute time per GPU.
    print('## GPUs, total compute time', file=output_file)
    pt = df.drop_duplicates(subset=['epoch', 'gpu_id'], keep='last').pivot_table('interval', 'gpu_id', aggfunc='sum')
    pt['% use'] = (pt['interval'] / (timespan)).apply(lambda x: f'{x:.1%}')
    if sort_by_use:
        pt = pt.sort_values('interval', ascending=False).reset_index()
    pt['interval'] = pt['interval'].apply(human_time)
    print(pt.to_markdown(colalign=('left', 'right', 'right')), file=output_file)
    print(file=output_file)

# Creates a visualization of GPU utilization and saves it to a file.
def plot(df, plot_file, slices):
    if len(df) == 0:
        print('No data to plot')
        return

    import seaborn as sns
    from matplotlib import pyplot as plt

    # Determine the time range and interval for plotting.
    start_time = df['epoch'].min()
    end_time = df['epoch'].max()
    end_time += df[df['epoch'] == end_time].interval.mean()
    timespan = int(end_time - start_time)

    interval = timespan // slices
    module = slices // 50

    # Set up a placeholder for idle GPU usage.
    idle_name = '_idle_'
    users = list(df['user'].unique()) + [idle_name]
    to_numbers = {name: id for id, name in enumerate(users)}
    idle_idx = to_numbers[idle_name]

    idles = list()
    fake_gpu_id = len(df['gpu_id'].unique())
    for i in range(slices):
        idles.append({"epoch": start_time + i * interval, "user": idle_name, 'gpu_id': fake_gpu_id})

    idle_df = pd.DataFrame(idles, columns=['epoch', 'user', 'gpu_id'])
    idle_df['datetime'] = pd.to_datetime(idle_df['epoch'], unit='s')
    df = pd.concat([df, idle_df]).reset_index(drop=True)

    # Reshape the data for plotting.
    df = df.set_index(['datetime', 'gpu_id', 'user'])
    df = df.groupby([pd.Grouper(level='datetime', freq=f'{interval}s'),
                     pd.Grouper(level='gpu_id'), pd.Grouper(level='user')]).first().index.to_frame(index=False)

    df['user_id'] = df['user'].map(to_numbers)

    # Determine the maximum number of concurrent users.
    max_concurrent = df.pivot_table('user_id', ['gpu_id'], 'datetime', aggfunc='count').max()
    max_concurrent = np.lcm.reduce(list(max_concurrent.to_numpy(dtype=int)))

    # Create a heatmap for visualization.
    pt = df.pivot_table('user_id', ['gpu_id', 'user'], 'datetime').fillna(users.index(idle_name))
    num_gpus = len(df['gpu_id'].unique()) - 1
    user_map = np.zeros(shape=(max_concurrent * num_gpus, pt.shape[1]))
    for gpu_id in range(num_gpus):
        gpu_pt = pt.loc[gpu_id]
        for time, col in enumerate(gpu_pt):
            gpu_users = list(set(gpu_pt[col].unique()).difference([idle_idx]))
            if len(gpu_users) == 0:
                user_map[gpu_id * max_concurrent:((gpu_id + 1) * max_concurrent), time] = idle_idx
            else:
                bar_size = max_concurrent // len(gpu_users)
                for i, gpu_user in enumerate(gpu_users):
                    user_map[gpu_id * max_concurrent + bar_size * i:((gpu_id + 1) * max_concurrent), time] = gpu_user

    # Format the x-axis labels with readable dates.
    def date_format(x):
        d = datetime.fromisoformat(str(x))
        return d.strftime("%Y-%m-%d %H:%M")

    plt.figure(figsize=(20, 5))

    cmap = sns.color_palette("deep", len(users) - 1)
    cmap.append(sns.crayons['White'])

    ax = sns.heatmap(user_map, cmap=cmap)
    xticklabels = [date for i, date in enumerate(pt.rename(date_format, axis='columns')) if i % module == 0]
    ax.set_xticks([i * module for i in range(len(xticklabels))])
    ax.set_xticklabels(xticklabels)
    xticklabels = ax.get_xticklabels()
    for label in xticklabels:
        label.set_rotation(90)

    yticklabels = [f'GPU{i}' for i in range(num_gpus)]
    ax.set_yticks([i * max_concurrent + max_concurrent / 2 for i in range(num_gpus)])
    ax.set_yticklabels(yticklabels)
    for i in range(1, num_gpus):
        ax.axhline(y=i * max_concurrent, color='w', linewidth=2)

    colorbar = ax.collections[0].colorbar
    r = colorbar.vmax - colorbar.vmin
    colorbar.set_ticks([colorbar.vmin + 0.5 * r / (len(users)) + r * i / (len(users)) for i in range(len(users))])
    colorbar.set_ticklabels(users)

    plt.tight_layout()
    plt.savefig(plot_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_gpus', type=int, default=0,
                        help='Number of GPUs (default: it is inferred from log)')
    parser.add_argument('--input_file', type=argparse.FileType('rt', encoding='utf-8'), default=sys.stdin,
                        help='Input file, (default: standard input)')
    parser.add_argument('--output_file', type=argparse.FileType('wt', encoding='utf-8'), default=sys.stdout,
                        help='Output file (default: standard output)')
    parser.add_argument('--plot_file', type=str, default=None,
                        help='Plot user/GPU map to file (default: no plot). The filename extension determines the output format (e.g.: .pdf/.png/.svg)')
    parser.add_argument('--plot_slices', type=int, default=250,
                        help='Number of time slices in the plot (default: 250)')
    parser.add_argument('--user_map', type=str, default=None,
                        help='Mapping of user names to alternative names. One per line, format: "user,newname" (default: no mapping)')
    parser.add_argument("--sort-by-use", action="store_true", help="Sort table by descending use in the report (default: sort by name)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--last-year", action="store_true", help="Process logs from the last year. This and the following options are mutually exclusive (default: process the whole input data)")
    group.add_argument("--last-month", action="store_true", help="Process logs from the last month")
    group.add_argument("--last-week", action="store_true", help="Process logs from the last week")
    group.add_argument("--last-day", action="store_true", help="Process logs from the last day")
    group.add_argument("--last-hour", action="store_true", help="Process logs from the last hour")
    group.add_argument("--interval", nargs=2, metavar=('START', 'END'),
                       help="Process logs within the given start and end date (using ISO 8601 format: 2024-12-26T12:30:00)")

    args = parser.parse_args()

    # Load input data into a DataFrame.
    input_file = args.input_file

    df = pd.read_csv(input_file, header=None,
                     names=["epoch", "interval", "gpu_id", "gpu_util", "used_memory", "pid", "user", "cmdline"])
    df['datetime'] = pd.to_datetime(df['epoch'], unit='s')

    # Filter data based on specified time intervals.
    if args.interval:
        start_time = pd.to_datetime(args.interval[0])
        end_time = pd.to_datetime(args.interval[1])
        df = df[(df['datetime'] >= start_time) & (df['datetime'] <= end_time)]
    else:
        start_time = None
        if args.last_year:
            start_time = pd.Timestamp.now() - pd.DateOffset(years=1)
        elif args.last_month:
            start_time = pd.Timestamp.now() - pd.DateOffset(months=1)
        elif args.last_week:
            start_time = pd.Timestamp.now() - pd.DateOffset(weeks=1)
        elif args.last_day:
            start_time = pd.Timestamp.now() - pd.DateOffset(days=1)
        elif args.last_hour:
            start_time = pd.Timestamp.now() - pd.DateOffset(hours=1)
        if start_time is not None:
            df = df[df['datetime'] >= start_time]

    unknown_user = '<unknown>'

    if args.user_map:
        user_map = dict()
        with (open(args.user_map, mode='rt', encoding='utf-8') as input_file):
            for line in input_file:
                line = line.strip()
                if len(line) == 0:
                    continue
                old_name, new_name = line.split(',')
                user_map[old_name] = new_name
            df['user'] = df['user'].map(user_map)

    missing_user_pids = df[df['user'].isna()]['pid'].unique()
    # Group by 'pid' and find the most frequent 'user' for each
    most_common_users = df.dropna(subset=['user']).groupby('pid')['user'].agg(lambda x: x.value_counts().idxmax())
    # Map the most common users to the missing values
    mask = df['pid'].isin(missing_user_pids) & df['user'].isna()
    df.loc[mask, 'user'] = df.loc[mask, 'pid'].map(most_common_users)

    df['user'] = df['user'].fillna(unknown_user)

    report(df, args.num_gpus, args.output_file, args.sort_by_use)

    if args.plot_file:
        plot(df, args.plot_file, args.plot_slices)


if __name__ == '__main__':
    main()
