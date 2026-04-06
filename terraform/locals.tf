locals {
  labels = {
    app         = "chat-streaming-pipeline"
    environment = var.environment
    owner       = var.owner_label
  }

  dead_letter_topic = (
    var.dead_letter_topic_name == null || var.dead_letter_topic_name == ""
  ) ? "${var.topic_name}-dlq" : var.dead_letter_topic_name
}
