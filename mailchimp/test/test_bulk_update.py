from unittest.mock import patch
import pytest

from mailchimp.services import (
    MailchimpBulkUpdateError,
    MailchimpTimeOutError,
    wait_for_completion,
)


def test_wait_for_completion():
    with patch("mailchimp_marketing.Client") as mock_client:
        instance = mock_client.return_value
        return_value = {"status": "finished"}
        instance.batches.status.return_value = return_value
        wait_for_completion(instance, "test", "test")


def test_wait_for_completion_several_passes():
    with patch("mailchimp_marketing.Client") as mock_client:
        instance = mock_client.return_value
        return_pending = {"status": "pending"}
        return_completed = {"status": "finished"}
        instance.batches.status.side_effect = [
            return_pending,
            return_pending,
            return_completed,
        ]
        wait_for_completion(instance, "test", "test")


def test_wait_for_completion_status_error():
    with patch("mailchimp_marketing.Client") as mock_client:
        instance = mock_client.return_value
        return_value = {"status": "unknown"}
        instance.batches.status.return_value = return_value
        with pytest.raises(MailchimpBulkUpdateError):
            wait_for_completion(instance, "test", "test")


def test_wait_for_completion_time_out_error():
    with patch("mailchimp_marketing.Client") as mock_client:
        instance = mock_client.return_value
        return_value = {"status": "pending"}
        instance.batches.status.return_value = return_value
        with pytest.raises(MailchimpTimeOutError):
            wait_for_completion(instance, "test", "test")
