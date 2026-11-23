import json
import sys
import urllib.request

from hescom_bbps_api import normalize_bbps_response


def test_normalizes_pending_amount():
    payload = {
        "consumerNumber": "4509281734",
        "billDetails": {"billAmount": 674.00, "units": 412, "dueDate": "24/11/2026"},
        "status": "PENDING",
    }
    result = normalize_bbps_response(payload)
    assert result["consumerNo"] == "4509281734"
    assert result["amount"] == 674.00
    assert result["units"] == 412
    assert result["status"] == "PENDING"


def test_paid_bill_has_zero_pending_amount():
    result = normalize_bbps_response({"amountDue": 674.00, "status": "PAID"})
    assert result["amount"] == 0.0
    assert result["status"] == "PAID"


def test_api_test_endpoint():
    with urllib.request.urlopen("http://127.0.0.1:4180/api/hescom/test?consumer=4509281734", timeout=5) as response:
        data = json.loads(response.read().decode("utf-8"))
    assert data["ok"] is True
    assert data["bill"]["amount"] == 674.0


if __name__ == "__main__":
    test_normalizes_pending_amount()
    test_paid_bill_has_zero_pending_amount()
    test_api_test_endpoint()
    print("HESCOM BBPS API tests passed")
