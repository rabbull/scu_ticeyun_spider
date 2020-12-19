import requests
import bs4
import json
import sys

from config import VERBOSE_MODE, RETRY, COOKIES, HEADERS


def print_info(*args, **kwargs):
    if not VERBOSE_MODE:
        return
    print(*args, **kwargs)


class RoundEntity:
    def __init__(self, available: bool, record_id: str, item_id: str, name: str, date: str, time: str, num: str,
                 location: str, verification: str, booking_status: str):
        self.available = available
        self.record_id = record_id
        self.item_id = item_id
        self.name = name
        self.date = date
        self.time = time
        self.num = num
        self.location = location
        self.verification = verification
        self.booking_status = booking_status

    @staticmethod
    def parse_from_row(row: bs4.Tag):
        cols = row.find_all(name="td")
        available = "disabled" not in cols[0].find().attrs.keys()
        record_id = cols[0].find()['value']
        item_id = cols[1].text
        name = cols[2].text
        date = cols[3].text
        time = cols[4].text
        num = cols[5].text
        location = cols[6].text
        verification = cols[7].text
        booking_status = cols[8].text
        return RoundEntity(available, record_id, item_id, name, date, time, num, location, verification, booking_status)


def enroll(round_entity: RoundEntity):
    url = "http://scu.ticeyun.com/servlet/StudentServlet"
    form_data = {
        "itemId": round_entity.record_id.split("-")[0],
        "recordNum": round_entity.record_id.split("-")[1],
        "method": "saveTestBespeak",
        "studentNo": "2017141463010",
        "bespeak": "%E9%A2%84++%E7%BA%A6",
    }
    response = requests.post(url, form_data, headers=HEADERS, cookies=COOKIES)
    soup = bs4.BeautifulSoup(response.text, features="html.parser")
    alert_script = str(soup.find_all(name="script")[-1])
    clauses = alert_script.split()
    possible_splitters = ["\"", "'"]
    for clause in clauses:
        if clause.startswith("alert"):
            for splitter in possible_splitters:
                if clause.find(splitter) != -1:
                    message = clause.split(splitter)[1]
                    print_info("预约结果：", message)
                    return
    print_info("网站没有返回任何提示。")


def find_rounds() -> list:
    url = "http://scu.ticeyun.com/SportWeb/bespeak/testBespeak_query1.jsp"
    response = requests.get(url, headers=HEADERS, cookies=COOKIES)
    if response.text.find("页面已过期或者遇到错误") != -1:
        raise_cookie_not_set_error()
    soup = bs4.BeautifulSoup(response.text, features="html.parser")
    rows = soup.find(name="tr").find_all(name="tr")[2].find_all(name="tr")
    if len(rows) == 2:
        return []
    rows = rows[2:-1]
    round_entities = [RoundEntity.parse_from_row(row) for row in rows]
    return round_entities


def raise_cookie_not_set_error():
    print("Cookies 未设置或有误，请按 README 中说明进行设置", file=sys.stderr)
    exit(1)


def check_config():
    if len(COOKIES) != 2:
        raise_cookie_not_set_error()
    for key in COOKIES.keys():
        if COOKIES[key] == "":
            raise_cookie_not_set_error()


def main():
    check_config()
    i = 0
    while i == 0 or RETRY:
        i += 1
        print_info("第", i, "次尝试...")

        round_entities = find_rounds()
        if len(round_entities) == 0:
            print_info("没有找到任何场次。")
            continue
        print_info("找到了以下场次：")
        last_available_round = None
        for index, round_entity in enumerate(round_entities):
            if round_entity.available:
                last_available_round = round_entity
            print_info(index, json.dumps(round_entity.__dict__))
        if last_available_round is None:
            print_info("没有可预定场次。")
            # continue

        print_info("尝试预定其中最后一个场次...")
        enroll(round_entities[-1])


if __name__ == "__main__":
    main()
