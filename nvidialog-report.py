import argparse
import pandas as pd
import sys
from collections import defaultdict

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', type=argparse.FileType('rt', encoding='utf-8'), default=sys.stdin,
                        help='Input file, default is standard input')
    args = parser.parse_args()

    input_file = args.input_file

    df = pd.read_csv(input_file,header=None,names=["time_value", "interval", "gpu_id", "gpu_util", "used_memory", "pid", "owner", "cmdline"])

    start_time = df['time_value'].min()
    end_time = df['time_value'].max()
    timespan = end_time-start_time

    print('# Report')
    print()
    print('## Users, by-GPU time')
    print(df.pivot_table('interval',['owner','gpu_id'], aggfunc='sum').to_markdown())
    print()
    print('## Users, total number of processes')
    print(df.groupby('owner')['pid'].nunique().to_markdown())
    print()
    print('## Users, total time (use of multiple GPUs sum up)')
    print(df.pivot_table('interval','owner', aggfunc='sum').to_markdown())
    print()
    print('## GPUs, total time (use by multiple users sum up)')
    print(df.pivot_table('interval','gpu_id', aggfunc='sum').to_markdown())
    print()
