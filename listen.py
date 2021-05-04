import schedule
import time
from prepare import add_state, initialise_document
from const import madrid_elecciones_2019, madrid_elecciones_2021



def listen_to_history():
    state_path = "state.json"
    initialise_document(state_path, madrid_elecciones_2021, "2021", madrid_elecciones_2019, "2019")
    schedule.every(30).seconds.do(lambda: add_state(madrid_elecciones_2021, "2021", state_path="state.json", check_state=True))

    while True:
        schedule.run_pending()
        time.sleep(1)


def fake_listen():
    schedule.every(10).seconds.do(lambda: add_state(madrid_elecciones_2019, "2021", state_path="fake.json", check_state=False))

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    # fake_listen()
    listen_to_history()