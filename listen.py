import schedule
import time
from prepare import add_state
from const import madrid_elecciones_2019

schedule.every(10).seconds.do(lambda: add_state(madrid_elecciones_2019, "2021", state_path="fake.json", check_state=False))

while True:
    schedule.run_pending()
    time.sleep(1)