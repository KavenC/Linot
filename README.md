# Linot
[![Join the chat at https://gitter.im/KavenC/Linot](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/KavenC/Linot?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Linot is a chat bot for [LINE](http://line.me/)&trade; App. It provides services to user through the LINE message interfaces.

Contact: leave message on gitter or [twitter@nevak](https://twitter.com/nevak)

## Update
**2015-08-29** Python LINE API package has been pulled down from Github by official request from Naver. It should be a clear sign that the owner of LINE (a.k.a Naver Corps.) is not allowing custom LINE chat bot being made and run. In response to current situation, I decide to halt Linot development until I find another communication interface (perhaps Whatsapp?). 

Any code contributions are still always welcomed. 

## Services
###  TwitchNotifier
TwitchNotifier let user subscribe twitch channels. When the subscribed channels goes live, Linot sends a LINE message to the subscribers with the channel infomation.
* Example<br>
```
User> twitch -subscribe Nightblue3
Linot> Done.
(When Nightblue3 goes live)
Linot>
Nightblue3 is now streamming!!
[Title] ASSASSIN/SATED JUNGLE META
[Playing] League of Legends
http://www.twitch.tv/nightblue3
```
* Command List<br>
```
User> twitch -h
```

## Installation & Run
1. This bot is run under **Python2.7**. You will also need [LINE API](http://carpedm20.github.io/line/) package. 
2. Please notice that there is currently an issue on the [thrift](https://github.com/apache/thrift) which may randomly connection lost when using LINE API. Please refere to this [thread](https://github.com/carpedm20/LINE/issues/9).
3. Fill out generate_config.py and generate the config file.
  - Since it is a LINE chat bot, you need to provide a valid LINE account/password.
  - If you are going to load TwitchNotifier, you need to provide a oauth key to a twitch account.
4. To run the bot: `python run.py`
* You may need to enter the pompt code to the LINE app on your cellphone to complete the authentication process.

## Run Tests
1. We use nose to write test cases, make sure you have nose installed. ex: `pip install nose`
2. Run test cases by: `nosetests -c nose.cfg`
