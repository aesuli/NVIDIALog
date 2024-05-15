import argparse
import sys
from datetime import timedelta, datetime

import numpy as np
import pandas as pd


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


def report(df, num_gpus, output_file):
    start_time = df['epoch'].min()
    end_time = df['epoch'].max()
    end_time += df[df['epoch'] == end_time].time.mean()
    timespan = int(end_time - start_time)

    if num_gpus == 0:
        num_gpus = int(df['gpu_id'].nunique())

    print(
        f'# Report ({datetime.fromtimestamp(end_time).strftime("%Y-%m-%d %H:%M")} - {datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M")})',
        file=output_file)
    print(f'Duration: {human_time(timespan)}', file=output_file)
    print(file=output_file)
    print(f'Number of GPUs: {num_gpus}', file=output_file)
    print(file=output_file)
    print(f'Total available compute time: {human_time(timespan * num_gpus)}', file=output_file)
    print(file=output_file)
    print('## User-GPU time', file=output_file)
    pt = df.pivot_table('time', ['user', 'gpu_id'], aggfunc='sum')
    pt['% use'] = (pt['time'] / timespan).apply(lambda x: f'{x:.1%}')
    pt['time'] = pt['time'].apply(human_time)
    print(pt.reset_index()
          .rename(columns={'idx1': '', 'idx2': ''}).to_markdown(index=False,
                                                                colalign=('left', 'left', 'right', 'right')),
          file=output_file)
    print(file=output_file)
    print('## Users, number of processes', file=output_file)
    print(df.rename(columns={'pid': 'num processes'}).groupby('user')['num processes'].nunique().to_markdown(),
          file=output_file)
    print(file=output_file)
    print('## Users, total compute time', file=output_file)
    pt = df.drop_duplicates(subset=['epoch', 'user', 'gpu_id'], keep='last').pivot_table('time', 'user',
                                                                                         aggfunc='sum')
    pt['% use'] = (pt['time'] / (timespan * num_gpus)).apply(lambda x: f'{x:.1%}')
    pt['time'] = pt['time'].apply(human_time)
    print(pt.to_markdown(colalign=('left', 'right', 'right')), file=output_file)
    print(file=output_file)
    print('## GPUs, total compute time', file=output_file)
    pt = df.drop_duplicates(subset=['epoch', 'gpu_id'], keep='last').pivot_table('time', 'gpu_id', aggfunc='sum')
    pt['% use'] = (pt['time'] / (timespan)).apply(lambda x: f'{x:.1%}')
    pt['time'] = pt['time'].apply(human_time)
    print(pt.to_markdown(colalign=('left', 'right', 'right')), file=output_file)
    print(file=output_file)


def plot(df, plot_file, slots=200):
    import seaborn as sns
    from matplotlib import pyplot as plt

    start_time = df['epoch'].min()
    end_time = df['epoch'].max()
    end_time += df[df['epoch'] == end_time].time.mean()
    timespan = int(end_time - start_time)

    interval = timespan / slots // 60

    df = df.set_index(['datetime', 'gpu_id', 'user'])
    df = df.groupby([pd.Grouper(level='datetime', freq=f'{interval}min'),
                     pd.Grouper(level='gpu_id'), pd.Grouper(level='user')]).first().index.to_frame(index=False)

    idle_name = '_idle_'
    users = list(df['user'].unique()) + [idle_name]
    to_numbers = {name: id for id, name in enumerate(users)}
    idle_idx = to_numbers[idle_name]

    df['user_id'] = df['user'].map(to_numbers)

    max_concurrent = int(df.pivot_table('user_id', ['gpu_id'], 'datetime', aggfunc='count').max().max())

    pt = df.pivot_table('user_id', ['gpu_id', 'user'], 'datetime').fillna(users.index(idle_name))

    num_gpus = len(df['gpu_id'].unique())
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

    def date_format(x):
        d = datetime.fromisoformat(str(x))
        return d.strftime("%Y-%m-%d %H:%M")

    plt.figure(figsize=(20, 5))

    cmap = sns.color_palette("deep", len(users) - 1)
    cmap.append(sns.crayons['White'])

    ax = sns.heatmap(user_map, cmap=cmap)
    xticklabels = [date for i, date in enumerate(pt.rename(date_format, axis='columns')) if i % 4 == 0]
    ax.set_xticks([i * 4 for i in range(len(xticklabels))])
    ax.set_xticklabels(xticklabels)

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
                        help='Number of GPUs. Optional, by default it is inferred from log.')
    parser.add_argument('--input_file', type=argparse.FileType('rt', encoding='utf-8'), default=sys.stdin,
                        help='Input file, default is standard input')
    parser.add_argument('--output_file', type=argparse.FileType('wt', encoding='utf-8'), default=sys.stdout,
                        help='Output file, default is standard output')
    parser.add_argument('--plot_file', type=str, default=None,
                        help='Plot user/GPU map to file. Default is no plot.')
    parser.add_argument('--user_map', type=str, default=None,
                        help='Mapping of user names to alternative names. One per line, format: "user,newname". Default is no mapping.')
    args = parser.parse_args()

    input_file = args.input_file

    df = pd.read_csv(input_file, header=None,
                     names=["epoch", "time", "gpu_id", "gpu_util", "used_memory", "pid", "user", "cmdline"])
    df['datetime'] = pd.to_datetime(df['epoch'], unit='s')

    if args.user_map:
        user_map = dict()
        with (open(args.user_map,mode='rt',encoding='utf-8') as input_file):
            for line in input_file:
                old_name,new_name = line.strip().split(',')
                user_map[old_name] = new_name
        df['user'] = df['user'].map(user_map)

    report(df, args.num_gpus, sys.stdout)

    if args.plot_file:
        plot(df, args.plot_file)


if __name__ == '__main__':
    main()
