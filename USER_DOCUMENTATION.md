# NowSecure Appvetting Slack Bot - User Guide

## Overview

The NowSecure Appvetting bot automates security assessment workflows in Slack by:
- Automatically downloading PDF reports when assessments complete
- Allowing you to trigger new app security assessments directly from Slack
- Providing real-time status updates and notifications

## Automatic Report Downloads

### How It Works

When NowSecure Platform completes a security assessment, it posts a notification to your monitored Slack channel. The bot automatically:

1. Detects the assessment notification
2. Downloads the PDF security report from NowSecure
3. Posts the PDF as a threaded reply for easy access

### What You'll See

**Successful Assessment:**
- PDF report attached to the thread with the filename `report-{assessment-id}.pdf`
- Comment: "PDF report for app '{app-name}'"

**Failed Assessment:**
- Error message in the thread: "Assessment failed, please check the NowSecure Platform for details and contact NowSecure support if needed."
- Technical team notification for investigation

## Triggering New Assessments

### Command Syntax

```
/appvetting new <client_tag> <app-store-url>
```

### Parameters

**client_tag**
- Short identifier for your customer/client (e.g., `AFP`, `Schindler`, `Fannie_Mae`)
- Use underscores instead of spaces
- Must be an actual client name (not placeholder text like "clienttag")

**app-store-url**
- Full URL from Apple App Store or Google Play Store
- Must be the complete URL including `https://`

### Examples

**iOS App:**
```
/appvetting new Schindler https://apps.apple.com/us/app/rakuten-viber-messenger/id382617920
```

**Android App:**
```
/appvetting new Fannie_Mae https://play.google.com/store/apps/details?id=com.sadadcompany.sadad&hl=en_IN&pli=1
```

**International iOS App:**
```
/appvetting new AFP https://apps.apple.com/fr/app/leboncoin/id484115113
```

### Response Messages

**Success:**
```
✅ iOS app `com.example.app` referred by <url> submitted for assessment.
Status: pending
```

**Errors:**
- `❌ Invalid URL` - URL format is incorrect or cannot be parsed
- `❌ Invalid URL or unable to extract package name/bundle ID` - Cannot identify app from URL
- `❌ Invalid app ID` - iOS app not found in iTunes
- `❌ Unable to retrieve bundle ID` - iTunes API error
- `❌ Invalid App Store URL` - URL is not from Apple App Store or Google Play Store
- `❌ Missing client_tag or URL parameter` - Incomplete command
- `❌ Too many parameters` - Extra parameters provided
- `❌ Invalid client_tag parameter` - Using placeholder value instead of actual client name
- `❌ Failed to submit [platform] app for assessment. Error: [reason]` - NowSecure API error

### Assessment Status Values

- `pending` - Assessment queued and will start shortly
- `BINARY_UNAVAILABLE` - App binary temporarily unavailable (bot will retry automatically after 60 seconds)
- `BINARY_RESTORING` - App binary being restored (bot will retry automatically after 60 seconds)

## Supported App Stores

### Apple App Store (iOS)
- URLs starting with `https://apps.apple.com/`
- Supports all country-specific stores (us, fr, uk, etc.)
- Bot automatically resolves the numeric App ID to bundle identifier

### Google Play Store (Android)
- URLs starting with `https://play.google.com/store/apps/`
- All regional variations supported
- Package name extracted directly from URL

## Getting Help

Type `/appvetting` (without parameters) or `/appvetting help` to display the help message in Slack.

## Important Notes

1. **Assessment Time**: After submission, assessments typically take time to complete. You'll receive a notification in the channel when the report is ready.

2. **Rate Limiting**: If you submit multiple assessments rapidly, the NowSecure API may rate-limit requests. The bot handles this automatically with retries.

3. **Binary Availability**: Sometimes app binaries are temporarily unavailable from app stores. The bot automatically retries these cases after a short delay.

4. **Report Size Validation**: The bot verifies PDF reports are valid before posting. Unusually small reports (< 120KB) indicate assessment failures and trigger error handling.

5. **Thread Organization**: All reports are posted as threaded replies to keep channels organized. Click "X replies" to view the PDF.

6. **Activity Logging**: All `/appvetting` commands are logged with timestamp, client tag, and URL for audit purposes.

## Troubleshooting

**Bot doesn't respond to assessment notifications:**
- Verify the bot has been added to the channel
- Check that notifications are from "NowSecure Platform" bot

**Command fails with error:**
- Verify URL format matches examples above
- Ensure client_tag contains no spaces (use underscores)
- Check that app exists in the specified app store

**Assessment submission succeeds but no report appears:**
- Assessment is still in progress - wait for notification
- Check NowSecure Platform directly for assessment status
- Failed assessments will generate error notifications
