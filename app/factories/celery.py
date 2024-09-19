# from app.factories.extensions import celery
#
#
# def setup_celery(app):
#     celery.conf.update(
#         broker_url=app.config['CELERY_BROKER_URL']
#     )
#     celery.conf.update(app.config)
#     TaskBase = celery.Task
#
#     class ContextTask(TaskBase):
#         abstract = True
#
#         def __call__(self, *args, **kwargs):
#             with app.app_context():
#                 return TaskBase.__call__(self, *args, **kwargs)
#
#     celery.Task = ContextTask
#     return celery
