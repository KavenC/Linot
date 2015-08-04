import pickle
LinotConfig = {
    # Line
    'line_account': 'your@line.account',
    'line_password': 'linepassword',
    'line_comp_name': 'ComputerNameForLoginLine',  # Anything you want
    'admin_id': 'TheAdminLineId',
    # Twitch
    'twitch_oauth': 'TwitchOauthKey',
    'twitch_user': 'TwitchUserName',
}
pickle.dump(LinotConfig, open("config.p", "wb"))
