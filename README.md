# welcome dialogue
Our new onboarding-system, replacing [verification-listener](https://github.com/Info-Bonn/verification-listener).  

Single-guild discord-bot to give roles to a member accepting your servers rules.  
Also sending a neat little welcome message to the user as well as buttons to select basic roles.    
The selection can also be done on a channel on the server. Where an entrypoint button is sent by the bot.  

The bot also runs a task all five minutes to ensure that no member is missed due to potential downtime or other errors.   
It's possible to ignore members that joined before a specific date if the system shall not apply to older members.  

## Setup

###### Setup a [venv](https://docs.python.org/3/library/venv.html) (optional, but recommend)
`python3 -m venv venv`   
`source venv/bin/activate` 


##### Using pip to install the bot as editable package:  
` python3 -m pip install -e .`  
`export TOKEN="your-key"`  
`discord-bot`  
##### Or using the launch script:  
`pip install -r requirements.txt`  
`export TOKEN="your-key"`   
`python3 ~/git/discord-bot/launcher.py`  

### Configure the roles map
The role options in the button menu are read from a json. The default path is `data/role_buttons.json` (see env variables).  
The json mapping of the form:
```json
{
    "<guild_id>": {
        "role_buttons": {
            "<button_text1>": 6666666666666666666,
            "<button_text2>": 9999999999999999999
          
        }
    }
}
```
Replace `<guild_id>` and `<button_text*>` with your guilds id and the text you want to display.  
The mapped numbers are the role-id of the role that shall be given if the button is pressed.  
Note: The bot is still single server. It will only load the first guild-key from the json, which has to match the guild set in your config!  
The layered mapping is for easier migration when the bot might get multi-server support.

### Intents
The bot uses all intents by default, those are required for such simple things like 'display member-count at startup'.  
You need to enable those intents in the [discord developers portal](https://discord.com/developers/applications) 
under `*YourApplication*/Bot/Privileged Gateway Intents`.   
It's possible reconfigure the requested intents in `main.py` if you don't need them.  
But I'd suggest using them all for the beginning, especially if you're relatively new to discord.py.  
This will only be an issue if your bot reaches more than 100 servers, then you've got to apply for those intents. 

#### Optional env variables
| parameter |  description |
| ------ |  ------ |  
| `export ROLES="760434164146634752"`  | Roles to give after verification, separated by a space |
| `export ROLE_OPTION_FILE="data/role_buttons.json"`| Roles to give after verification, separated by a space |
| `export GUILD="760421261649248296"`  | Guild the bot shall be set up for |
| `export START_CHANNEL="760429072156459019"`  | Channel the bot mentions in welcome message |
| `export ONBOARDING_CHANNEL="1015975768045670501"` | Channel for interaction buttons on guild |
| `export ONBOARDING_ROLE="1015975563250372698"` | Role member has only during onboarding 
| `export PREFIX="b!"`  | Command prefix |
| `export CHECK_PERIOD="5"` | Time between two checks for missed members |
| `export NOT_BEFORE="25.08.2021"`  | Members joined before that date won't be captured by verification check task |
| `export OWNER_NAME="unknwon"` | Name of the bot owner | |
| `export OWNER_ID="100000000000000000"` | ID of the bot owner |

The shown values are the default values that will be loaded if nothing else is specified.  
Expressions like `{PREFIX}` will be replaced by during loading the variable and can be used in specified env variables.

Set those variables using env-variables (suggested):  
`export PREFIX="b!"`  
Or use a json-file expected at: `./data/config.json` like:  
```json
{
  "TOKEN": "[your-token]",
  "PREFIX": "b!"
}
```

_If a variable is set using env and json **the environment-variable replaces the json**!_
