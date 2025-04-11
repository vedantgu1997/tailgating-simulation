import argparse
import pandas as pd
import numpy as np
from pathlib import Path

def generate_episode_data(df):
    df['Time Stamp'] = pd.to_datetime(df['Time Stamp'])

    episodes = []
    open_indices = df[df['Door Opened'] == 1].index
    close_indices = df[df['Door Closed'] == 1].index

    close_ptr = 0
    for open_idx in open_indices:
        open_time = df.loc[open_idx, 'Time Stamp']

        # Find the next close event within 180s
        close_time = None
        for i in range(close_ptr, len(close_indices)):
            candidate_time = df.loc[close_indices[i], 'Time Stamp']
            duration = (candidate_time - open_time).total_seconds()
            if 1 < duration < 180:
                close_time = candidate_time
                close_ptr = i + 1
                break

        # Get slice of episode
        if close_time:
            mask = (df['Time Stamp'] >= open_time) & (df['Time Stamp'] <= close_time)
            duration = (close_time - open_time).total_seconds()
            outlier = 0
        else:
            mask = (df['Time Stamp'] >= open_time)
            close_time = pd.NaT
            duration = np.nan
            outlier = 1

        episode_df = df[mask]

        num_entries = episode_df['User ID'].nunique()

        tailgating_detected = int((episode_df['Tailgating Detected'] == 1).any())
        feedback = episode_df['Human Feedback'].mode()[0] if not episode_df['Human Feedback'].isna().all() else 'Unknown'
        generation_logic = episode_df['Generation Logic'].mode()[0] if not episode_df['Generation Logic'].isna().all() else 'Unknown'
        human_explanation = episode_df['Human Logic explaining the feedback for the episode'].mode()[0] if not episode_df['Human Logic explaining the feedback for the episode'].isna().all() else 'Unknown'


        hour = open_time.hour
        is_weekend = int(open_time.weekday() >= 5)

        episodes.append({
            'Start Time': open_time,
            'End Time': close_time,
            'Duration': duration,
            'Number of Entries': num_entries,
            'Hour of Day': hour,
            'Weekend': is_weekend,
            'Tailgating Detected': tailgating_detected,
            'Human Feedback': feedback,
            'Generation Logic': generation_logic,
            'Human Explanation': human_explanation,
            'Outlier Flag': outlier
        })

    return pd.DataFrame(episodes)

def main():
    parser = argparse.ArgumentParser(description='Extract episode features from simulated door access data.')
    parser.add_argument('--data', type=str, required=True, help='Path to the extracted data file')

    args = parser.parse_args()
    input_path = Path(args.data)
    output_path = Path('data/episode_data.csv')

    if not input_path.exists():
        raise FileNotFoundError(f"Input file {input_path} not found.")

    # Load data
    df = pd.read_csv(input_path)

    # Extract episodes
    episode_df = generate_episode_data(df)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save
    episode_df.to_csv(output_path, index=False)
    print(f"Episode data saved to {output_path}")

if __name__ == "__main__":
    main()
