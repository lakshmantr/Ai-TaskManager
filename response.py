import random
def get_response(intent, success=True, task=None):
    responses = {
        "add_task": {
            True:[
                f"Added '{task}' to your task list.",
                f"I’ve saved the new task '{task}'.",
                f"The task '{task}' has been created successfully.",
                f"'{task}' has been added to your tasks."
            ]
        },
        "update_task": {
            True: [
                f"The task '{task}' has been updated.",
                f"I’ve made the necessary changes to '{task}'.",
                f"'{task}' is now up to date.",
            ],
            False: [
                f"I couldn’t find '{task}' to update.",
                f"Unable to make changes to '{task}'. Please check the task name.",
                f"'{task}' doesn’t seem to exist. Could you try again?",
            ],
        },
        "delete_task": {
            True: [
                f"Deleted the task '{task}'.",
                f"'{task}' has been removed successfully.",
                f"The task '{task}' is no longer in your list.",
            ],
            False: [
                f"I couldn’t find '{task}' to delete.",
                f"'{task}' doesn’t exist, so I couldn’t delete it.",
                f"Unable to remove '{task}'. Please check your task name.",
            ],
        },
        "invalid_input": {
            True: [
                "That doesn’t seem like a valid request.",
                "I couldn’t understand that. Could you rephrase?",
                "Sorry, I didn’t catch what you meant. Try again with a valid command.",
                "That’s not a recognized task command.",
                "Please make sure you’re asking about adding, updating, deleting, or checking tasks.",
                "I’m not sure what that means in the context of your task manager.",
            ],
        }
    }
    return random.choice(responses[intent][success])