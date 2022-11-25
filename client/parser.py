import pandas as pd

df = pd.read_csv('results1.csv')
df['time'] = df['time'].astype(float)

# print(df.to_stri  ng()) 

send_df = df.loc[df['type'] == "Sent"]
receive_df = df.loc[df['type'] == "Received"]

# print(send_df.to_string())

send_total = send_df['time'].sum()
receive_total = receive_df['time'].sum()
# print(len(send_df.index))

latency = (receive_total - send_total) / len(send_df.index)

print(f"Latency = {latency}")


window = 1

delta = 0.05
t = 0
input_count = 0
input_sum = 0
input_end = send_df['time'].max()
while t+window <= input_end:
    n = len(send_df.loc[(t <= send_df['time']) & (send_df['time'] < t+window)].index)
    input_sum += n
    input_count += 1
    t += delta

Input_throughput = input_sum / input_count*window
print(f"Input Throughput = {Input_throughput}")


t = 0
output_count = 0
output_sum = 0
output_end = receive_df['time'].max()
while t+window <= output_end:
    n = len(receive_df.loc[(t <= receive_df['time']) & (receive_df['time'] < t+window)].index)
    output_sum += n
    output_count += 1
    t += delta

Output_throughput = output_sum / output_count*window
print(f"Output Throughput = {Output_throughput}")