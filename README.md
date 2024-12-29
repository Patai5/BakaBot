# BakaBot

Discord Bot and Web Scraper for the Czech online schooling system "Bakaláři".\
Receive instant updates on new grades and schedule changes directly in your Discord!

#### Note:
This application wasn't initially designed for seamless integration with different Bakaláři instances.\
You might need to adjust a few variables to adapt it to your specific school version:

Subjects in this file:
* constants.py

And urls in these:
* grades.py
* schedule.py
* utils.py

## Usage examples

- #### 📅 Get immediate Discord notifications for any changes detected in your school schedule
  - View changes presented in user-friendly HTML/CSS generated images using [Pyppeteer](https://github.com/pyppeteer/pyppeteer)
> <img src="https://github.com/Patai5/BakaBot/assets/87543374/9202f5e7-5de2-4aa8-b2f2-22bdeba96c34">

- #### 📚 Stay informed about your latest grades 💀
> ![image](https://github.com/Patai5/BakaBot/assets/87543374/cc230f15-d44b-4742-9685-6586a61c8e07)
![image](https://github.com/Patai5/BakaBot/assets/87543374/46b49ae1-4255-461b-95a1-52c12846b883)

- #### ☀️ Receive daily morning notifications about the day's schedule
> ![image](https://github.com/Patai5/BakaBot/assets/87543374/d940eeef-87c4-4c52-a4c0-35b7c896d75c)

- #### ⏰ Get notifed about the upcoming lessons
> ![image](https://github.com/Patai5/BakaBot/assets/87543374/17414be4-ffda-4356-8e98-5205e3bd6bc9)

- #### 🌐 Keep track of Bakaláři server's online status
> ![image](https://github.com/Patai5/BakaBot/assets/87543374/30cc91a8-c21d-431e-ad66-38539ae9f640)

- #### 📆 Use the `/schedule` command to get the schedule for any specific day
> ![image](https://github.com/Patai5/BakaBot/assets/87543374/27d9e048-12fe-42c8-903d-51854008ba32)

## Instalation

1. Clone the repository
2. Setup your `.env` file from `.env.example`
    - Guide on how to get the YOUR DISCORD TOKEN can be found [here](https://www.writebots.com/discord-bot-token/).
        - Aditionally you have to turn on all three options under "Privileged Gateway Intents" which can be found under the Bot option on left hand side.
    - Guide on how to get the YOUR DISCORD ID can be found [here](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID).
3. Create a virtual environment _(not required, but well recommended)_

```sh
python -m venv env
```

4. Start the virtual environment

```sh
env\Scripts\activate.bat
```

5. Install dependencies
```sh
pip install -e .
```
    _(If you're contributing to the project, install development dependencies:)_
    ```sh
    pip install -e .[dev]
    ```
6. Install Playwright

```sh
playwright install
```

7. Start the bot
```sh
python -m src.main
```
