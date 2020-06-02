from flask import render_template
from flask_classy import FlaskView, route


class SchedulesView(FlaskView):
    @route('/shuttle-stats')
    def stats(self):
        return render_template('/schedules/shuttle_stats.html')