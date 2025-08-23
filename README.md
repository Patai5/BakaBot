# BakaBot

**BakaBot** is a Discord bot and web scraper designed for the Czech online schooling system **Bakaláři**. Receive real-time updates on new grades, schedule changes, and more directly in your Discord server!

---

## ⚠️ Not Maintained Anymore

This project is no longer maintained as I no longer have access to the Bakaláři system... Feel free to fork and modify it for your own use though :)

Anyway, here are some of the funniest bits of code I somehow managed to write along the way :P I started on this project back when I was just learning to code, so there are still some _gems_ left inside:

-   <details><summary>`return min(fieldsLen, 4) - 1` the professional way 😎</summary>
    https://github.com/Patai5/BakaBot/blob/913958aa1cae584fb6816ae8d932bb299efb5443/src/core/predictor.py#L169-L178
    </details>
-   <details><summary>Files >>> PostgreSQL + MongoDB combined 🗿</summary>
    https://github.com/Patai5/BakaBot/blob/913958aa1cae584fb6816ae8d932bb299efb5443/src/utils/utils.py#L23-L26
    https://github.com/Patai5/BakaBot/blob/913958aa1cae584fb6816ae8d932bb299efb5443/src/utils/utils.py#L14-L20
    </details>
-   <details><summary>🪜🎢 `tab`➡️`tab`➡️`tab`➡️ (only 8 indentation deep 🥱)</summary>
    https://github.com/Patai5/BakaBot/blob/913958aa1cae584fb6816ae8d932bb299efb5443/src/bot_commands/reactions.py#L108-L119
    honorable mentions 🥀
    https://github.com/Patai5/BakaBot/blob/913958aa1cae584fb6816ae8d932bb299efb5443/src/bot_commands/reactions.py#L35-L46
    https://github.com/Patai5/BakaBot/blob/913958aa1cae584fb6816ae8d932bb299efb5443/src/message_timers.py#L148-L159
    </details>
-   <details><summary>Old commit from when main.py was still at its peak 😭🙏</summary>
    https://github.com/Patai5/BakaBot/blob/b4135ae91a26ff9ddba22b9bcb29909373093431/main.py
    </details>

---

## Features

-   📅 **Schedule Notifications**: Get real-time Discord notifications when your school schedule changes.
-   📚 **Grade Alerts**: Stay up to date with your latest grades, delivered directly to your Discord.
-   ☀️ **Daily Schedule Reminders**: Receive notifications each morning with your schedule for the day.
-   ⏰ **Upcoming Lessons Alerts**: Be notified about upcoming lessons and events.
-   🌐 **Bakaláři Server Status**: Monitor the current status of your Bakaláři server.
-   📆 **Custom Schedule Requests**: Use the `/schedule` command to fetch your schedule for any given day.

## Usage examples

-   #### 📅 Get immediate Discord notifications for any changes detected in your school schedule
    View changes presented in user-friendly HTML/CSS generated images using [Pyppeteer](https://github.com/pyppeteer/pyppeteer)

> ![image](https://github.com/Patai5/BakaBot/assets/87543374/9202f5e7-5de2-4aa8-b2f2-22bdeba96c34)

-   #### 📚 Stay informed about your latest grades 💀
    Get instant updates on your grades with easy-to-read notifications.

> ![image](https://github.com/Patai5/BakaBot/assets/87543374/cc230f15-d44b-4742-9685-6586a61c8e07) > ![image](https://github.com/Patai5/BakaBot/assets/87543374/46b49ae1-4255-461b-95a1-52c12846b883)

-   #### ☀️ Receive daily morning notifications about the day's schedule
    Start your day with a helpful reminder of your upcoming lessons.

> ![image](https://github.com/Patai5/BakaBot/assets/87543374/d940eeef-87c4-4c52-a4c0-35b7c896d75c)

-   #### ⏰ Get notifed about the upcoming lessons
    Receive timely alerts for upcoming lessons to stay prepared.

> ![image](https://github.com/Patai5/BakaBot/assets/87543374/17414be4-ffda-4356-8e98-5205e3bd6bc9)

-   #### 🌐 Keep track of Bakaláři server's online status
    Monitor the server status to check if Bakaláři is online.

> ![image](https://github.com/Patai5/BakaBot/assets/87543374/30cc91a8-c21d-431e-ad66-38539ae9f640)

-   #### 📆 Use the `/schedule` command to get the schedule for any specific day
    Easily fetch the schedule for any day with a simple command.

> ![image](https://github.com/Patai5/BakaBot/assets/87543374/27d9e048-12fe-42c8-903d-51854008ba32)

## Instalation

1. **Clone the repository**:

    ```bash
    git clone https://github.com/Patai5/BakaBot.git
    cd BakaBot
    ```

2. **Setup your `.env` file**:

    Copy the example `.env` file and configure it with your Discord bot credentials.

    ```bash
    cp .env.example .env
    ```

    - **Discord Token**: [How to get your Discord token](https://www.writebots.com/discord-bot-token/)
        - Don’t forget to enable all three Privileged Gateway Intents (found under the "Bot" settings).
    - **Discord ID**: [How to get your Discord ID](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID)

3. **Create a virtual environment** (Optional but recommended)

    ```bash
    python -m venv env
    ```

4. **Activate the virtual environment**:

    - On Windows:
        ```bash
        env\Scripts\activate.bat
        ```
    - On macOS/Linux:
        ```bash
        source env/bin/activate
        ```

5. **Install dependencies**:

    ```bash
    pip install -e .
    ```

    _(If you're contributing to the project, install development dependencies)_

    ```bash
    pip install -e .[dev]
    ```

6. **Install Playwright**:

    ```bash
    playwright install
    ```

7. **Start the bot**:

    ```bash
    python -m src.main
    ```

8. **Setup the bot**:
   Once the bot is running, use the `/setup` command in your Discord server to configure it.

## Docker

To run the bot using Docker, execute:

```bash
docker-compose up --build -d
```
