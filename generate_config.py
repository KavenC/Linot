import pickle
if __name__ == '__main__':
    LinotConfig = {
        'interface': {
            'line': {
                'account': 'line_account',
                'password': 'line_password',
                'admin_id': 'line_admin_id',
                'comp_name': 'LinotMaster',
            },
        },
        'service': {
            'twitch': {
                'oauth': 'twitch_bot_account_oauth',
                'user': 'twitch_bot_account_name',
            },
        },
    }
    pickle.dump(LinotConfig, open("config.p", "wb"))
