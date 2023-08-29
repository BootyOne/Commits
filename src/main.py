import os
import aiohttp
import asyncio
from typing import NoReturn
from config import GITHUB_USERNAME, COMPANY_NAME
from collections import defaultdict
import matplotlib as mpl
import matplotlib.pyplot as plt


async def fetch(session, url, auth):
    async with session.get(url, auth=aiohttp.BasicAuth(auth[0], auth[1])) as response:
        return await response.json()


async def fetch_commits(session, repo, auth, counter):
    commit_page = 1
    while True:
        commit_url = repo["commits_url"][0:-6] + f"?page={commit_page}"
        commit_info = await fetch(session, commit_url, auth)
        if not commit_info:
            break
        commit_page += 1
        for line in commit_info:
            message = line["commit"]["message"]
            if "Merge pull request #" not in message:
                email = line["commit"]["author"]["email"]
                counter[email] += 1


async def calculating_statistics(_name: str, _token: str, _company: str):
    counter = defaultdict(int)

    async with aiohttp.ClientSession() as session:
        page = 1
        while True:
            url = f"https://api.github.com/users/{_company}/repos?page={page}"
            repositories = await fetch(session, url, (_name, _token))
            page += 1
            if not repositories:
                break

            tasks = []
            for repo in repositories:
                task = fetch_commits(session, repo, (_name, _token), counter)
                tasks.append(task)

            await asyncio.gather(*[asyncio.create_task(task) for task in tasks])

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


async def main():
    token = os.environ.get('GITHUB_API_TOKEN')
    most_active_count = 0
    rest = 0

    title = f'{COMPANY_NAME}: соотношение коммитов 100 лучших и остальных (%)'
    counter = await calculating_statistics(GITHUB_USERNAME, token, COMPANY_NAME)
    most_active_sorted = sorted(counter.items(), key=lambda x: x[1], reverse=True)
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
    asyncio.run(main())
