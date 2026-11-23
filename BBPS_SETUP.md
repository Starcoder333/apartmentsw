# HESCOM Live BBPS Integration

## Start the API layer

```powershell
Set-Location "c:\Anand\Aprtmentsw\apartmentsw"
$env:BBPS_API_URL="https://authorized-bbps-provider.example/api/bill-fetch"
$env:BBPS_API_TOKEN="your-secret-token"
$env:BBPS_BILLER_ID="HESCOM"
python hescom_bbps_api.py
```

## Start SocietyPay

```powershell
python -m http.server 4173
```

Open `http://localhost:4173/index.html`, go to **Bills/EB**, and select **Live Fetch**. Enter the HESCOM Account/RR/Consumer number.

## Test locally

```powershell
$env:BBPS_TEST_MODE="1"
python hescom_bbps_api.py

python test_hescom_bbps.py
```

The test mode returns a clearly marked fixture and must not be enabled in production.

## Amount behavior

- `PENDING` bill: SocietyPay displays the returned outstanding/pending amount.
- `PAID` bill: amount is forced to `₹0.00` and meter status is `PAID`.
- The total in Bills/EB includes only meters whose status is `PENDING`.

BBPS credentials must come from an authorized bill-payment/Bill Aggregator provider. HESCOM should be queried only through the provider's fetch-bill API and not by scraping or CAPTCHA bypass.
