/**
 * Report Download Functions with Loading Indicators
 * Issue #130: Add visual feedback for long-running report generation
 *
 * Handles PDF and CSV report downloads with loading spinners.
 * Uses fetch API to trigger downloads without page navigation.
 */

/**
 * Download PDF report with loading spinner
 * @param {number} chatId - The chat ID for the report
 */
function downloadPDFReport(chatId) {
  const button = document.getElementById('download_pdf_report');
  const spinner = document.getElementById('pdf-spinner');
  const buttonText = document.getElementById('pdf-text');

  // Show spinner and update UI
  spinner.style.display = 'inline-block';
  buttonText.textContent = 'Generating PDF...';
  button.disabled = true;

  // Trigger download via fetch
  fetch(`/chat/${chatId}/download-pdf/`)
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.blob();
    })
    .then(blob => {
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `interview_report_${chatId}.pdf`;
      document.body.appendChild(a);
      a.click();

      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      // Hide spinner and restore button
      spinner.style.display = 'none';
      buttonText.textContent = 'Download as PDF';
      button.disabled = false;
    })
    .catch(error => {
      console.error('PDF download error:', error);
      alert('Failed to generate PDF. Please try again.');

      // Hide spinner and restore button on error
      spinner.style.display = 'none';
      buttonText.textContent = 'Download as PDF';
      button.disabled = false;
    });
}

/**
 * Download CSV report with loading spinner
 * @param {number} chatId - The chat ID for the report
 */
function downloadCSVReport(chatId) {
  const button = document.getElementById('download_csv_report');
  const spinner = document.getElementById('csv-spinner');
  const buttonText = document.getElementById('csv-text');

  // Show spinner and update UI
  spinner.style.display = 'inline-block';
  buttonText.textContent = 'Generating CSV...';
  button.disabled = true;

  // Trigger download via fetch
  fetch(`/chat/${chatId}/download-csv/`)
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.blob();
    })
    .then(blob => {
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `interview_report_${chatId}.csv`;
      document.body.appendChild(a);
      a.click();

      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      // Hide spinner and restore button
      spinner.style.display = 'none';
      buttonText.textContent = 'Download as CSV';
      button.disabled = false;
    })
    .catch(error => {
      console.error('CSV download error:', error);
      alert('Failed to generate CSV. Please try again.');

      // Hide spinner and restore button on error
      spinner.style.display = 'none';
      buttonText.textContent = 'Download as CSV';
      button.disabled = false;
    });
}
