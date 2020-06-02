from flask import render_template
from flask_classy import FlaskView, route


class SchedulesView(FlaskView):
    @route('/shuttle-stats')
    def stats(self):
        return render_template('/schedules/shuttle_stats.html')

    @route('/request-shuttle')
    def request(self):
        return render_template('/schedules/request_shuttle.html')

    @route('/shuttle-schedules')
    def schedule(self):
        return render_template('schedules/shuttle_schedules.html')

    @route('/driver-check-in')
    def check_in(self):
        return render_template('schedules/shuttle_driver_check_in.html')
