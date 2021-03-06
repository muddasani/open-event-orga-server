import icalendar
import pytz
from flask import url_for
from icalendar import Calendar, vCalAddress, vText
from sqlalchemy import asc

from app.models.event import Event as EventModel
from app.models.session import Session
from app.helpers.signals import event_json_modified, speakers_modified, sessions_modified


class ICalExporter:
    def __init__(self):
        pass

    @staticmethod
    def export(event_id):
        """Takes an event id and returns the event in iCal format"""

        event = EventModel.query.get(event_id)

        cal = Calendar()
        cal.add('prodid', '-//fossasia//open-event//EN')
        cal.add('version', '2.0')
        cal.add('x-wr-calname', event.name)
        cal.add('x-wr-caldesc', "Schedule for sessions at " + event.name)

        tz = event.timezone or 'UTC'
        tz = pytz.timezone(tz)

        sessions = Session.query \
            .filter_by(event_id=event_id) \
            .filter_by(state='accepted') \
            .filter(Session.deleted_at.is_(None)) \
            .order_by(asc(Session.starts_at)).all()

        for session in sessions:

            if session and session.starts_at and session.ends_at:
                event_component = icalendar.Event()
                event_component.add('summary', session.title)
                event_component.add('uid', str(session.id) + "-" + event.identifier)
                event_component.add('geo', (event.latitude, event.longitude))
                event_component.add('location', session.microlocation.name or '' + " " + event.location_name)
                event_component.add('dtstart', tz.localize(session.starts_at))
                event_component.add('dtend', tz.localize(session.ends_at))
                event_component.add('email', event.email)
                event_component.add('description', session.short_abstract)
                event_component.add('url', url_for('event_detail.display_event_detail_home',
                                                   identifier=event.identifier, _external=True))

                for speaker in session.speakers:
                    # Ref: http://icalendar.readthedocs.io/en/latest/usage.html#file-structure
                    # can use speaker.email below but privacy reasons
                    attendee = vCalAddress('MAILTO:' + event.email if event.email else 'undefined@email.com')
                    attendee.params['cn'] = vText(speaker.name)
                    event_component.add('attendee', attendee)

                cal.add_component(event_component)

        return cal.to_ical()


@speakers_modified.connect
@sessions_modified.connect
@event_json_modified.connect
def ical_export_celery(app, **kwargs):
    from app.helpers.tasks import export_ical_task
    export_ical_task.delay(kwargs['event_id'])
