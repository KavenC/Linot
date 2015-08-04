# Linot
Linot is a chat bot for [LINE](http://line.me/)&trade; App. It provides services to user through the LINE message interfaces. 

It is currently demo on LineID: **LinotBot**

## Services
###  TwitchNotifier
TwitchNotifier let user subscribe twitch channels. When the subscribed channels goes live, Linot sends a LINE message to the subscribers with the channel infomation.
* Example<br>
    `User> twtich -subscribe Nightblue3`<br>
    `Linot> Done.`<br>
    (When Nightblues3 goes live)<br>
    `Linot>`<br>
    `Nightblue3 is now streamming!!`<br>
    `[Title] ASSASSIN/SATED JUNGLE META`<br>
    `[Playing] League of Legends`<br>
    `http://www.twitch.tv/nightblue3`<br>
* Command List<br>
    `User> twitch -h`

## Installation & Run
1. This bot is run under **Python2.7**. You will also need [LINE API](http://carpedm20.github.io/line/) package. 
2. Please notice that there is currently an issue on the [thrift](https://github.com/apache/thrift) which may randomly connection lost when using LINE API. Please refere to this [thread](https://github.com/carpedm20/LINE/issues/9).
3. Fill out ConfigPickle.py and generate the config file.
  - Since it is a LINE chat bot, you need to provide a valid LINE account/password.
  - If you are going to load TwitchNotifier, you need to provide a oauth key to a twitch account.
4. To run the bot: `python run.py`
* You may need to enter the pompt code to the LINE app in your cellphone to complete the authentication process.
