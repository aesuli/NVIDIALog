import argparse
from datetime import timedelta, datetime

import pandas as pd
import sys


def human_time(seconds):
    td = timedelta(seconds=seconds)
    years = td.days // 365
    months = (td.days % 365) // 30
    days = (td.days % 365) % 30
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    seconds = (td.seconds % 3600) % 60

    if years>0:
        output = f'{years}y '
    else:
        output = ''
    if months>0:
        output += f'{months:2}M '
    else:
        output += ''
    if days>0:
        output += f'{days:2}d '
    else:
        output += ''
    if hours > 0:
        output += f'{hours:2}h '
    else:
        output += ''
    if minutes>0:
        output += f'{minutes:2}m '
    else:
        output += ''
    if seconds>0:
        output += f'{seconds:2}s'
    else:
        output += ''

    return output

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', type=argparse.FileType('rt', encoding='utf-8'), default=sys.stdin,
                        help='Input file, default is standard input')
    parser.add_argument('--num_gpus', type=int, default=0,
                        help='Number of GPUs. Optional, by default it is inferred from log.')
    args = parser.parse_args()

    input_file = args.input_file

    df = pd.read_csv(input_file,header=None,names=["time_stamp", "time", "gpu_id", "gpu_util", "used_memory", "pid", "user", "cmdline"])
    start_time = df['time_stamp'].min()
    end_time = df['time_stamp'].max()
    end_time += df[df['time_stamp']==end_time].time.mean()
    timespan = int(end_time-start_time)

    if args.num_gpus > 0:
        num_gpus = args.num_gpus
    else:
        num_gpus = int(df['gpu_id'].nunique())

    print('# Report')
    print(f'Start date: {datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S")}')
    print()
    print(f'End date: {datetime.fromtimestamp(end_time).strftime("%Y-%m-%d %H:%M:%S")}')
    print()
    print(f'Duration: {human_time(timespan)}')
    print()
    print(f'Number of GPUs: {num_gpus}')
    print()
    print(f'Total available compute time: {human_time(timespan*num_gpus)}')
    print()

    print('## User-GPU time')
    pt = df.pivot_table('time',['user','gpu_id'], aggfunc='sum')
    pt['% use'] = (pt['time']/timespan).apply(lambda x: f'{x:.1%}')
    pt['time'] = pt['time'].apply(human_time)
    print(pt.reset_index()
          .rename(columns={'idx1': '', 'idx2': ''}).to_markdown(index=False,colalign=('left','left','right','right')))
    print()

    print('## Users, number of processes')
    print(df.rename(columns={'pid':'num processes'}).groupby('user')['num processes'].nunique().to_markdown())
    print()

    print('## Users, total compute time (use of multiple GPUs sum up)')
    pt = df.pivot_table('time','user', aggfunc='sum')
    pt['% use'] = (pt['time']/(timespan*num_gpus)).apply(lambda x: f'{x:.1%}')
    pt['time'] = pt['time'].apply(human_time)
    print(pt.to_markdown(colalign=('left','right','right')))
    print()

    print('## GPUs, total compute time (use by multiple users sum up)')
    pt = df.pivot_table('time', 'gpu_id', aggfunc='sum')
    pt['% use'] = (pt['time']/(timespan*num_gpus)).apply(lambda x: f'{x:.1%}')
    pt['time'] = pt['time'].apply(human_time)
    print(pt.to_markdown(colalign=('left','right','right')))
    print()
