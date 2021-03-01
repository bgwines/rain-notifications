import asyncio
import datetime
import os
import python_weather
import smtplib
import ssl
import subprocess


SENDER_EMAIL = "hellyeahbird@gmail.com"
TARGET_EMAILS = ["brettwines@gmail.com"]

PRECIP_THRESHOLD_PCT = 20
N_DAYS_IN_ADVANCE_TO_NOTIFY = 1  # 0 <= x <= 3


def find(p, xs):
    for x in xs:
        if p(x):
            return x
    return None


def get_message(forecast):
    noun = "day" if N_DAYS_IN_ADVANCE_TO_NOTIFY == 1 else "days"
    return """Subject: Precipitation warning
In %d %s (%s), there is a %d percent chance of precipitation. The forecast is %s
 and %d (%d..%d). Please consider covering the exercise equipment on the balcony
and moving the clipboard inside.""" % (N_DAYS_IN_ADVANCE_TO_NOTIFY, noun,
    forecast._date, forecast.precip, forecast.sky_text, forecast.temperature,
    forecast.low, forecast.high)


async def main():
    client = python_weather.Client(format=python_weather.IMPERIAL)
    try:
        weather = await client.find("Mountain View CA")

        now = datetime.datetime.today()
        forecast = find(
            lambda day: (day.date - now).days == N_DAYS_IN_ADVANCE_TO_NOTIFY,
            weather.forecast)
        assert forecast, ("Could not find forecasted day "
            f"{N_DAYS_IN_ADVANCE_TO_NOTIFY} days in advance. Forecast: "
            f"{weather.forecast}")

        if forecast.precip > PRECIP_THRESHOLD_PCT:
            message = get_message(forecast)
            print(message)
            send_email(message)
        else:
            print(f"Precip threshold not reached: {forecast.date} "
                f"{forecast.precip}")
    except Exception as e:
        send_email(f"Failed with {e}")
    finally:
        await client.close()


def read_password():
    out = subprocess.run(["cat", "bird_password"], stdout=subprocess.PIPE)
    return out.stdout.strip().decode()


def send_email(message):
    port = 465  # For SSL
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login("hellyeahbird@gmail.com", read_password())
        for target_email in TARGET_EMAILS:
            server.sendmail(SENDER_EMAIL, target_email,
                f"{message}\n\nhell yeah")


if __name__ == '__main__':
    asyncio.run(main())
