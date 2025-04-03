const { google } = require('googleapis');

async function addPersonalLogRecord() {
  try {
    // Load credentials and create auth client
    const auth = new google.auth.GoogleAuth({
      keyFile: 'path/to/your/credentials.json',
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });

    const client = await auth.getClient();
    const sheets = google.sheets({ version: 'v4', auth: client });

    // Your spreadsheet ID - you can get this from the URL of your spreadsheet
    const spreadsheetId = 'YOUR_SPREADSHEET_ID';
    const range = 'harsh!A:Z'; // Worksheet name is 'harsh'

    // Example data to append
    const values = [
      ['Date', 'Entry'], // Replace with your actual column headers
      [new Date().toISOString(), 'Your log entry here']
    ];

    const request = {
      spreadsheetId,
      range,
      valueInputOption: 'USER_ENTERED',
      insertDataOption: 'INSERT_ROWS',
      resource: {
        values,
      },
    };

    const response = await sheets.spreadsheets.values.append(request);
    console.log('Record added successfully:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error adding record:', error);
    throw error;
  }
}

module.exports = { addPersonalLogRecord }; 