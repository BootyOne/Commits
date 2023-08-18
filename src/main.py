from config import GITHUB_USERNAME, COMPANY_NAME

import os
from typing import NoReturn

import requests
import matplotlib as mpl
import matplotlib.pyplot as plt


def calculating_statistics(_name: str, _token: str, _company: str) -> dict:
    counter = dict()
    page = 1
    while True:
        url = f"https://api.github.com/users/{_company}/repos?page={page}"
        repositories = requests.get(url=url, auth=(_name, _token)).json()
        page += 1
        if not repositories:
            break
        for repository in repositories:
            commit_page = 1
            while True:
                commit_url = repository["commits_url"][0:-6] + f"?page={commit_page}"
                commit_info = requests.get(url=commit_url, auth=(_name, _token)).json()
                if not commit_info:
                    break
                commit_page += 1
                for line in commit_info:
                    message = line["commit"]["message"]
                    if "Merge pull request #" not in message:
                        email = line["commit"]["author"]["email"]
                        if email in counter:
                            counter[email] += 1
                        else:
                            counter[email] = 1
                    else:
                        continue
    return counter


def chart_output(data_name: list, data_value: list, _title: str) -> NoReturn:
    dpi = 80
    fig = plt.figure(dpi=dpi, figsize=(1024 / dpi, 768 / dpi))
    mpl.rcParams.update({'font.size': 9})
    plt.title(_title)
    plt.pie(
        data_value,
        autopct='%.1f',
        radius=1.1,
        explode=[0.15] + [0 for _ in range(len(data_name) - 1)]
    )
    plt.legend(
        bbox_to_anchor=(-0.16, 0.45, 0.25, 0.25),
        loc='lower left',
        labels=data_name
    )
    fig.savefig('pie.png')


def main():
    token = os.environ.get('GITHUB_API_TOKEN')
    most_active_count = 0
    rest = 0
    title = f'{COMPANY_NAME}: соотношение коммитов 100 лучших и остальных (%)'
    most_active_sorted = sorted(
        calculating_statistics(GITHUB_USERNAME, token, COMPANY_NAME).items(),
        key=lambda x: x[1], reverse=True
    )
    for i in range(len(most_active_sorted)):
        if i < 100:
            print(f"{i + 1}. {most_active_sorted[i][0]} - {most_active_sorted[i][1]} commits")
            most_active_count += most_active_sorted[i][1]
        else:
            rest += most_active_sorted[i][1]
    data_names = ["Top 100", "Rest"]
    data_values = [most_active_count, rest]
    chart_output(data_names, data_values, title)


if __name__ == "__main__":
    main()
