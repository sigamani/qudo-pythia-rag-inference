import json

from .models.trial import Trial


def deserialize(data, trial_id=None):
    data["segmentation"] = f'qudo_{data["segmentation"].lower().replace(" ", "_")}'
    data["segment"] = f'{data["segmentation"]}_{data["segment"]}'
    trial = Trial.from_json(json.dumps(data))
    trial.id = trial_id
    return trial


def serialize(trial):
    trial_json = trial.to_clean_json_dict(follow_reference=False)
    return trial_json


def serialize_trial_message(message):
    message_dict = {
        "content": message.content,
        "role": message.role,
        "is_visible": message.is_visible,
        "is_bot": message.is_bot,
    }
    return message_dict
