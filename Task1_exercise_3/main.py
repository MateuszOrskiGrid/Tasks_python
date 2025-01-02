"""
Imports
"""
import argparse
from collections import Counter
import gzip
import logging

def parse_log_file(file_path):
    """
    Geeting right lines from file and checking general errors
    """
    user_agents = []
    try:
        with gzip.open(file_path, 'rt', encoding='utf-8') as file:
            for line in file:
                try:
                    parts = line.split('"')
                    if len(parts) > 5:
                        user_agent = parts[5].strip()
                        user_agents.append(user_agent)
                except IndexError as index_error:
                    logging.warning("Skipping malformed line: %s - %s", line.strip(), index_error)
                except UnicodeDecodeError:
                    logging.warning("Skipping line due to encoding issue")
    except (OSError, gzip.BadGzipFile) as file_error:
        logging.error("Error opening file %s: %s", file_path, file_error)

    return user_agents
def calculate_statistics(user_agents):
    """
    Calculation of unique users
    """
    user_agent_counter = Counter(user_agents)
    total_unique_user_agents = len(user_agent_counter)
    return total_unique_user_agents, user_agent_counter

def main():
    """
    Main parser
    """
    parser = argparse.ArgumentParser(description="Analyze access log for User Agent statistics.")
    parser.add_argument("file", type=str, help="Path to the access log file (gzipped).")
    args = parser.parse_args()
    user_agents = parse_log_file(args.file)
    total_unique_user_agents, user_agent_counter = calculate_statistics(user_agents)

    print(f"Total Unique User Agents: {total_unique_user_agents}")
    print("\nUser Agent Statistics:")
    for user_agent, count in user_agent_counter.most_common():
        print(f"{user_agent}: {count} requests")

if __name__ == "__main__":
    main()
