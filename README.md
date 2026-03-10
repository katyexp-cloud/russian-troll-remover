# troll-remover
-x-x-x-x-x-x-x-x-x-x-x- Scrapped, because most social platforms don't let you delete massive amount of comments regularly. Yes - by deleting bot comments by bot, you get flagged for bot activity -x-x-x-x-x-x-x-x-x-x-x-

<img width="1600" height="732" alt="image" src="https://github.com/user-attachments/assets/9ed527cd-42d5-43b3-aca0-a08a66684f90" />

# what's that?
- specialized bot that's scraping data from screen (non-API), analyze them via AI and deleting unwanted content
- using Hugging Face database (ROBeRTa for Czech) as word and context database (around 1GB)
- tracks sentiment, negativity, toxicity, argument value

# how does it work?
- user screenshots anchor points for the bot (target.png and target2.png)
- START: bot takes over mouse cursor and performs actions to highlight the individual text of the comment
- copies the highlighted text
- sends for AI analysis based on your settings
- performs actions to delete the comment or proceed to the next one
- waits until STOP

# features
- custom tweaking to detect not only Russian bots - Context and negative strings fields
- threshold value (sensitivity)
- automatic scrolling through the whole comment section
- 3 ROBeRTa models to choose from
- different speeds from 1 comment per 20s to 1 comment per 10s based on model
- automatic caching of most used phrases -> speed up to 1 comment per 3-5s
- blacklist to manually input blacklisted words -> speed up to 1 comment per 3s
- wobbly moves and different times simulating human-like cursor behaviour

# .jsons
-config.json
--saved settings
--manually configurate the actions

-blacklist.json
--manually input individual words to flag

-cache.json
--last 100 detected phrases cached for speed up the process

TO DO:
-pattern matching cache
-easy record move and click actions
-fully working stop button
-esc button
