import pandas as pd
import random
import yaml
import argparse
from datetime import datetime, timedelta
from pathlib import Path

def sample_scenario(weights_dict):
    keys = list(weights_dict.keys())
    weights = list(weights_dict.values())
    return random.choices(keys, weights=weights, k=1)[0]

def generate_biased_timestamp(start_date):
    day_offset = random.randint(0, 60)
    current_date = start_date + timedelta(days=day_offset)
    if random.random() < 0.8:
        while current_date.weekday() >= 5:
            day_offset += 1
            current_date = start_date + timedelta(days=day_offset)
    hour = random.randint(9, 17) if random.random() < 0.8 else random.randint(0, 23)
    minute = random.randint(0, 59)
    return datetime(current_date.year, current_date.month, current_date.day, hour, minute)

def generate_episode(episode_id, scenario_type, scenario_data, start_date):
    start_time = generate_biased_timestamp(start_date)
    duration = random.randint(*scenario_data["duration_range"])
    end_time = start_time + timedelta(seconds=duration)
    user_id = f"user_{random.randint(1, 200)}"

    events = [{
        "Time Stamp": start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "User ID": user_id,
        "Door Opened": 1,
        "Door Closed": 0,
        "Tailgating Detected": scenario_data["tailgating_detected"],
        "Human Feedback": scenario_data["human_feedback"],
        "Generation Logic": scenario_type,
        "Human Logic explaining the feedback for the episode": scenario_data["human_logic"]
    }]

    intermediate_times = sorted([
        start_time + timedelta(seconds=random.randint(1, duration - 1))
        for _ in range(random.randint(1, 3))
    ])
    for t in intermediate_times:
        events.append({
            "Time Stamp": t.strftime("%Y-%m-%d %H:%M:%S"),
            "User ID": user_id,
            "Door Opened": 0,
            "Door Closed": 0,
            "Tailgating Detected": scenario_data["tailgating_detected"],
            "Human Feedback": scenario_data["human_feedback"],
            "Generation Logic": scenario_type,
            "Human Logic explaining the feedback for the episode": scenario_data["human_logic"]
        })

    if scenario_type != "door_left_open":
        events.append({
            "Time Stamp": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "User ID": user_id,
            "Door Opened": 0,
            "Door Closed": 1,
            "Tailgating Detected": scenario_data["tailgating_detected"],
            "Human Feedback": scenario_data["human_feedback"],
            "Generation Logic": scenario_type,
            "Human Logic explaining the feedback for the episode": scenario_data["human_logic"]
        })

    return events

def main():
    random.seed(42)
    
    parser = argparse.ArgumentParser(description="Simulate door access episodes")
    parser.add_argument("--config", type=str, default="config/simulation_config.yaml", help="Path to YAML config")
    parser.add_argument("--episodes", type=int, help="Override total number of episodes")
    args = parser.parse_args()

    with open(args.config, "r") as file:
        config = yaml.safe_load(file)

    start_date = datetime.strptime(config["simulation"]["start_date"], "%Y-%m-%d %H:%M:%S")
    scenario_weights = config["scenario_weights"]
    scenario_configs = config["scenario_configs"]

    total_episodes = args.episodes if args.episodes else config["simulation"]["num_episodes"]

    all_rows = []
    cnt = {}
    for episode_id in range(total_episodes):
        scenario_type = sample_scenario(scenario_weights)
        cnt[scenario_type] = cnt.get(scenario_type, 0) + 1
        scenario_data = scenario_configs[scenario_type]
        all_rows.extend(generate_episode(episode_id, scenario_type, scenario_data, start_date))

    output_path = Path("data")
    output_path.mkdir(exist_ok=True)
    csv_path = output_path / "simulated_data.csv"

    df = pd.DataFrame(all_rows)
    df.sort_values(by="Time Stamp", inplace=True)
    df.to_csv(csv_path, index=False)

    print(f"Dataset saved at '{csv_path}'")
    print("Scenario counts:", cnt)
if __name__ == "__main__":
    main()
