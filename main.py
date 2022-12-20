import datetime

from PyQt5 import uic
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QHBoxLayout, QLabel, QPushButton
import sys
import requests as req
from PyQt5.QtGui import QPixmap, QIcon
import sqlite3

from PyQt5.uic.properties import QtWidgets

SCREEN_SIZE = [680, 480]

DATABASE_NAME = 'base.db'

con = sqlite3.connect(DATABASE_NAME)
cur = con.cursor()


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('interface.ui', self)
        self.text_weather_in_city.setText("Введите город выше")
        self.status_button = QPushButton(self)
        self.hide_all()
        self.flag_ = False
        self.buttonGet.clicked.connect(self.get_info)
        self.update_btn.clicked.connect(self.update_info)
        self.detail_btn.clicked.connect(self.detail_info)
        self.clear_btn.clicked.connect(self.hide_all)
        self.coords = []
        self.init_last_request()

    def init_last_request(self):
        request = cur.execute("SELECT city FROM recent_requests").fetchone()
        if request:
            self.get_info(input_city=request[0])

    def update_info(self) -> None:
        request = cur.execute("SELECT city FROM recent_requests").fetchone()
        if request:
            self.get_info(input_city=request[0], without_recommendation=True)
        return None

    def hide_all(self) -> None:
        #  Прячем всю информацию о погоде
        cur.execute("""DELETE FROM recent_requests""")
        self.text_weather_in_city.setText('Введите город')
        self.text_temp_2.hide()
        self.text_temp_likes.hide()
        self.text_pressure.hide()
        self.text_humidity.hide()
        self.text_speed_wind.hide()
        self.text_actually.hide()
        self.update_btn.hide()
        self.detail_btn.hide()
        self.clear_btn.hide()
        self.status_button.hide()
        return None

    def show_all(self, temp=None, temp_2=None,
                 humidity=None, wind_speed=None,
                 pressure=None, city_name=None):
        self.text_weather_in_city.setText(city_name)
        self.text_weather_in_city.setStyleSheet("QLabel {\n"
                                                "    color: black;\n"
                                                "}\n"
                                                "")
        self.text_temp_2.show()
        self.text_temp_2.setText("Температура: {}° C".format(temp))

        self.text_temp_likes.show()
        self.text_temp_likes.setText("По ощущениям: {}° C".format(temp_2))

        self.text_pressure.show()
        self.text_pressure.setText("Атмосферное давление {} мм рт. ст.".format(pressure))

        self.text_humidity.show()
        self.text_humidity.setText("Влажность: {}%".format(humidity))

        self.text_speed_wind.show()
        self.text_speed_wind.setText("Скорость ветра: {} м/с".format(wind_speed))

        self.text_actually.show()
        self.text_actually.setText("Актуально на: {}".format(datetime.datetime.now()))
        self.text_actually.setStyleSheet("QLabel {\n"
                                         "    color: black;\n"
                                         "font: 12pt \"Gotham Pro\";\n"
                                         "}\n"
                                         "")
        self.update_btn.show()
        self.detail_btn.show()
        self.clear_btn.show()
        self.status_button.show()
        return None

    def detail_info(self):
        request = cur.execute("SELECT city FROM recent_requests").fetchone()
        #  Получаем данные о погоде через API
        if request:
            response = req.get("http://api.openweathermap.org/data/2.5/weather",
                               params={'q': request[0], 'lang': 'ru',
                                       'units': 'metric',
                                       'APPID': "9d0864cfefebb1ec3592e7379f7776af"})
            weather = response.json()
            #  Выводим их в специлаьном всплывающем окне
            msg = QMessageBox()
            msg.setWindowTitle("Погода")
            msg.setText("За окнами {}\n"
                        "Температура: {} по цельсию".format(weather['weather'][0]['description'],
                                                            weather["main"]["temp"]))
            msg.setIcon(QMessageBox.Warning)

            msg.exec_()
        return None

    def get_weather_status(self, desc):
        if 'солнечно' in desc:
            return 'cолнечно'
        if 'туман' in desc:
            return 'туман'
        if 'облачн' in desc:
            return 'облачно'
        if 'снег' in desc:
            return 'снег'
        else:
            return 'дождь'

    def get_info(self, input_city=None, without_recommendation=None):
        city = self.inputCity.text() if not input_city else input_city
        #  Получаем данные о погоде через API
        response = req.get("http://api.openweathermap.org/data/2.5/weather",
                           params={'q': city, 'lang': 'ru',
                                   'units': 'metric',
                                   'APPID': "9d0864cfefebb1ec3592e7379f7776af"})
        weather = response.json()
        if "message" in weather.keys():
            try:
                #  Проверяем на ошибки ввода
                if weather["cod"] == "404":
                    self.text_weather_in_city.setText("Такого города не существует")
                    self.text_weather_in_city.setStyleSheet("QLabel {\n"
                                                            "    color: red;\n"
                                                            "}\n"
                                                            "")
                elif weather["cod"] == "400":
                    self.text_weather_in_city.setText("Город не указан")
                else:
                    self.text_weather_in_city.setText("Error")
                self.hide_all()
            except Exception as e:
                print(e)
                pass
        else:
            #  Вставляем в базу данных результат
            cur.execute("""DELETE FROM recent_requests""")
            cur.execute("""INSERT INTO recent_requests VALUES (?)""", (city,)).fetchall()
            con.commit()
            print(weather)
            self.show_all(city_name=city,
                          temp=weather["main"]["temp"],
                          temp_2=weather["main"]["feels_like"],
                          humidity=weather["main"]["humidity"],
                          wind_speed=weather["wind"]["speed"],
                          pressure=round(weather["main"]["pressure"] * 0.75))
            self.status_button.setIconSize(QSize(50, 50))
            self.status_button.setGeometry(0, 0, 40, 40)
            self.status_button.setIcon(QIcon(QPixmap("{}.png".format(self.get_weather_status(
                weather['weather'][0]['description']))))
            )
            self.status_button.show()
            if not without_recommendation:
                msg = QMessageBox()
                msg.setWindowTitle("Погода")
                temp = int(weather["main"]["temp"])
                #  Выводим рекомендации
                if temp < 10:
                    msg.setText(f"На улице довольно холодно: одевайтесь тепло.")
                elif temp < 20:
                    msg.setText(f"На улице холодно: одевайтесь потеплее.")
                else:
                    msg.setText(f"На улице тепло: одевайтесь свободно.")
                msg.setIcon(QMessageBox.Warning)

                msg.exec_()
            return None


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)
    return None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    sys.excepthook = except_hook
    ex = App()
    ex.setWindowTitle('Узнать погоду')
    ex.show()
    sys.exit(app.exec_())
