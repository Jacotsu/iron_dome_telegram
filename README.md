# Iron Dome Telegram
Iron dome is a program inspired by [mass ban telegram](https://github.com/egonalbrecht/mass_ban_telegram).
Its main purpose is to preemptively ban potentially hostile users from your groups.

## Usage

The software must be configured through its `settings.json`
```
{
    "api_id": 12345,
    "api_hash": "your api hash",
    "user_exceptions": [@username1, 123456],
    "groups_to_preserve": [@mygroup, "https://t.me/group_to_preseve"],
    "target_groups": [
	    "https://t.me/group_to_ban",
	    "@group_to_ban"
    ]
}
```
`user_exceptions` is a JSON list of users to not be included in your purge, useful if you have infiltrated agents
in hostile groups

After configuration, run `python3 scrape_users.py` to scrape the user data and save it to local files.
To initiate the purge, run `python3 purge.py`. This will ban all the scraped users that are not exempt from the
groups listed in `groups_to_preserve`

## Limitations
A the moment you can ban at most 300 users every 14:15 minutes, this is a limitation imposed by telegram.
The program will ban 300 users in 75 seconds and then wait 13 minutes, for large groups of users the average ban
ratio will be 1 user every 3 seconds; so for maximum efficiency it is recommended to distribute the workload
among multiple admins.
