import factory
from app.models.custom_placeholder import db, CustomPlaceholder
import app.factories.common as common


class CustomPlaceholderFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = CustomPlaceholder
        sqlalchemy_session = db.session

    name = common.string_
    origin = common.string_
    copyright = common.string_
    original_image_url = common.imageUrl_
