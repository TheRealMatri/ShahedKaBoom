Russian Bomber ☠️💣

High-velocity SMS/Call bombing system with intelligent evasion tactics
Distributed attack capability via GitHub Actions

https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram
https://img.shields.io/badge/Python-3.10%252B-blue?logo=python
https://img.shields.io/badge/License-MIT-yellow.svg

Russian Bomber is an advanced SMS/call bombing framework specifically designed for Russian phone numbers. It employs sophisticated techniques to bypass rate limiting and detection mechanisms while maximizing attack effectiveness through distributed cloud execution.

Features ✨
Multi-source proxy management (20+ public sources)

Markov chain-based request timing for evasion

Distributed attacks via GitHub Actions

Real-time Telegram monitoring

Three intensity levels (Hurricane, High, Stealth)

Automatic proxy rotation

User agent randomization

Dynamic request patterns

Detailed attack analytics

https://github.com/your_username/russian-bomber/blob/main/assets/dashboard.png?raw=true

How It Works ⚙️
Diagram
Code
graph TD
    A[Telegram Bot] -->|Start Command| B(Attack Type)
    B --> C{SMS Bombing}
    B --> D{Call Spam}
    B --> E{Cloud Attack}
    C --> F[Select Intensity]
    D --> F
    F --> G[Enter Phone Number]
    G --> H[Local Execution]
    E --> I[GitHub Actions]
    H --> J[Proxy Rotation]
    J --> K[Request Bombing]
    I --> K
    K --> L[Real-time Stats]
Installation 🛠️
Prerequisites
Python 3.10+

Telegram Bot Token (@BotFather)

GitHub Personal Access Token

Setup
Clone the repository:

bash
git clone https://github.com/your_username/russian-bomber.git
cd russian-bomber
Install dependencies:

bash
pip install -r requirements.txt
Create .env file:

ini
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_user_id
GH_TOKEN=your_github_personal_access_token
Run the bot:

bash
python app.py
Usage Guide 📲
Starting an Attack
Initiate with /start command

Choose attack type:

💣 SMS Bombing

📞 Call Spam

☁️ Cloud Attack (distributed)

Select intensity:

⚡️ Hurricane (10 min, max intensity)

🔥 High (15 min, balanced)

☁️ Stealth (30 min, low detection)

Enter target number in +7XXXXXXXXXX format

Monitoring Attacks
plaintext
🔥 АТАКА В ПРОЦЕССЕ 🔥

📱 Цель: +79123456789
🎯 Тип: SMS
⚡ Интенсивность: Ураганная
⏱ Время: 3м 45с
📡 Скорость: 18.7 req/сек
✅ Успешно: 342
❌ Ошибки: 28
📊 Успешность: 92.4%
🔰 Статус: АКТИВНА
Cloud Attack Setup
Fork this repository

Add secrets to your repository:

BOT_TOKEN

GH_TOKEN

Update REPO_OWNER and REPO_NAME in app.py

Enable GitHub Actions

Technical Architecture 🧠
Core Components
Proxy Manager

Fetches proxies from 20+ sources

Validates and rotates proxies

Automatic refresh every 30 minutes

Markov Request Timing

State-based timing algorithm

Three states: Normal, Burst, Cooldown

Dynamic delay adjustments

Distributed Execution

GitHub Actions workers

Parallel attack execution

Automatic scaling

Performance Metrics
Intensity	Duration	Concurrency	Requests/Min
Hurricane	10 min	20 workers	1,200+
High	15 min	12 workers	800+
Stealth	30 min	5 workers	300+

Ethical Considerations ⚖️
Warning
This project is intended for educational purposes only. The developers do not condone malicious use of this software. Always obtain proper authorization before testing any system. Unauthorized use may violate:

Computer Fraud and Abuse Act (CFAA)

Telecommunications regulations

Local privacy laws

License 📄
This project is licensed under the MIT License - see the LICENSE file for details.
