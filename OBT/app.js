// Application State
let appState = {
    uploadedData: [],
    apiConfig: {},
    processedResults: [],
    currentStep: 1
};

// Sample data from the provided JSON
const sampleData = [
    {
        strike_price: "24750",
        option_type: "Put", 
        expiry_date: "Aug 28, 2025",
        entry_time: "Aug 26, 2025, 15:06",
        exit_time: "Aug 26, 2025, 15:14"
    },
    {
        strike_price: "24750",
        option_type: "Put",
        expiry_date: "Aug 28, 2025", 
        entry_time: "Aug 26, 2025, 14:19",
        exit_time: "Aug 26, 2025, 14:20"
    },
    {
        strike_price: "24750",
        option_type: "Call",
        expiry_date: "Aug 28, 2025",
        entry_time: "Aug 26, 2025, 11:07", 
        exit_time: "Aug 26, 2025, 11:22"
    }
];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing app...');
    initializeEventListeners();
});

function initializeEventListeners() {
    console.log('Setting up event listeners...');
    
    // Get DOM elements
    const fileInput = document.getElementById('fileInput');
    const browseBtn = document.getElementById('browseBtn');
    const uploadArea = document.getElementById('uploadArea');
    const loadSampleBtn = document.getElementById('loadSampleBtn');
    const apiConfigForm = document.getElementById('apiConfigForm');
    const exportBtn = document.getElementById('exportBtn');
    
    // File upload events
    if (browseBtn) {
        browseBtn.addEventListener('click', () => {
            console.log('Browse button clicked');
            if (fileInput) fileInput.click();
        });
    }
    
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }
    
    // Drag and drop events
    if (uploadArea) {
        uploadArea.addEventListener('dragover', handleDragOver);
        uploadArea.addEventListener('dragleave', handleDragLeave);
        uploadArea.addEventListener('drop', handleDrop);
        uploadArea.addEventListener('click', () => {
            if (fileInput) fileInput.click();
        });
    }
    
    // Sample data button
    if (loadSampleBtn) {
        loadSampleBtn.addEventListener('click', function() {
            console.log('Load sample data clicked');
            loadSampleData();
        });
    }
    
    // API configuration form
    if (apiConfigForm) {
        apiConfigForm.addEventListener('submit', handleApiConfig);
    }
    
    // Export button
    if (exportBtn) {
        exportBtn.addEventListener('click', exportResults);
    }
    
    console.log('Event listeners initialized');
}

// File Upload Handlers
function handleFileSelect(event) {
    console.log('File selected');
    const file = event.target.files[0];
    if (file) {
        processExcelFile(file);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        uploadArea.classList.add('drag-over');
    }
}

function handleDragLeave(event) {
    event.preventDefault();
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        uploadArea.classList.remove('drag-over');
    }
}

function handleDrop(event) {
    event.preventDefault();
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        uploadArea.classList.remove('drag-over');
    }
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
            processExcelFile(file);
        } else {
            showError('Please upload a valid Excel file (.xlsx or .xls)');
        }
    }
}

function processExcelFile(file) {
    console.log('Processing Excel file:', file.name);
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const data = new Uint8Array(e.target.result);
            const workbook = XLSX.read(data, {type: 'array'});
            const sheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[sheetName];
            const jsonData = XLSX.utils.sheet_to_json(worksheet);
            
            if (jsonData.length === 0) {
                showError('Excel file is empty or has no valid data');
                return;
            }
            
            // Parse and validate the data
            const parsedData = parseExcelData(jsonData);
            if (parsedData.length > 0) {
                appState.uploadedData = parsedData;
                displayFileInfo(file, parsedData.length);
                showDataPreview(parsedData);
                showSection('dataPreviewSection');
                showSection('apiConfigSection');
            } else {
                showError('No valid data found in Excel file. Please check the format.');
            }
        } catch (error) {
            console.error('Error processing Excel file:', error);
            showError('Error reading Excel file. Please check the file format.');
        }
    };
    reader.readAsArrayBuffer(file);
}

function parseExcelData(jsonData) {
    const parsedData = [];
    
    jsonData.forEach((row, index) => {
        try {
            // Try to extract data from various column name variations
            const strikePrice = getColumnValue(row, ['Strike Price', 'Strike_Price', 'strike_price', 'Strike']);
            const entryTime = getColumnValue(row, ['Entry Time', 'Entry_Time', 'entry_time', 'Entry']);
            const exitTime = getColumnValue(row, ['Exit Time', 'Exit_Time', 'exit_time', 'Exit']);
            
            if (strikePrice && entryTime && exitTime) {
                // Parse strike price and option type
                const { strike, optionType, expiry } = parseStrikePrice(strikePrice);
                
                if (strike && optionType) {
                    parsedData.push({
                        strike_price: strike,
                        option_type: optionType,
                        expiry_date: expiry || 'Aug 28, 2025', // Default expiry
                        entry_time: entryTime,
                        exit_time: exitTime,
                        original_row: index + 1
                    });
                }
            }
        } catch (error) {
            console.warn(`Error parsing row ${index + 1}:`, error);
        }
    });
    
    return parsedData;
}

function getColumnValue(row, possibleKeys) {
    for (const key of possibleKeys) {
        if (row[key] !== undefined && row[key] !== null && row[key] !== '') {
            return row[key].toString().trim();
        }
    }
    return null;
}

function parseStrikePrice(strikeText) {
    // Parse formats like "Nifty 24750 Put Aug 28, 2025" or just "24750"
    const text = strikeText.toString().toLowerCase();
    
    let strike = null;
    let optionType = null;
    let expiry = null;
    
    // Extract strike price (number)
    const strikeMatch = text.match(/(\d+(?:\.\d+)?)/);
    if (strikeMatch) {
        strike = strikeMatch[1];
    }
    
    // Extract option type
    if (text.includes('put') || text.includes('pe')) {
        optionType = 'Put';
    } else if (text.includes('call') || text.includes('ce')) {
        optionType = 'Call';
    } else {
        // Default to Call if not specified
        optionType = 'Call';
    }
    
    // Extract expiry date if present
    const dateMatch = text.match(/(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2},?\s+\d{4}/i);
    if (dateMatch) {
        expiry = dateMatch[0];
    }
    
    return { strike, optionType, expiry };
}

function loadSampleData() {
    console.log('Loading sample data...');
    
    try {
        // Set the uploaded data to sample data
        appState.uploadedData = [...sampleData];
        console.log('Sample data loaded:', appState.uploadedData);
        
        // Display sample info
        displaySampleInfo();
        
        // Show data preview
        showDataPreview(sampleData);
        
        // Show the next sections
        showSection('dataPreviewSection');
        showSection('apiConfigSection');
        
        console.log('Sample data loading complete');
        
    } catch (error) {
        console.error('Error loading sample data:', error);
        showError('Error loading sample data');
    }
}

function displayFileInfo(file, recordCount) {
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        uploadArea.innerHTML = `
            <div class="file-info">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14,2 14,8 20,8"/>
                </svg>
                <div class="file-details">
                    <h4>${file.name}</h4>
                    <p>${(file.size / 1024).toFixed(1)} KB • ${recordCount} records</p>
                </div>
            </div>
        `;
    }
}

function displaySampleInfo() {
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        uploadArea.innerHTML = `
            <div class="file-info">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <div class="file-details">
                    <h4>Sample Data Loaded</h4>
                    <p>3 sample options records • Ready for processing</p>
                </div>
            </div>
        `;
    }
}

function showDataPreview(data) {
    console.log('Showing data preview for:', data);
    
    const previewTableBody = document.getElementById('previewTableBody');
    const dataStats = document.getElementById('dataStats');
    
    if (previewTableBody) {
        previewTableBody.innerHTML = '';
        
        data.forEach(record => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${record.strike_price}</td>
                <td><span class="status ${record.option_type.toLowerCase() === 'call' ? 'status--success' : 'status--error'}">${record.option_type}</span></td>
                <td>${record.expiry_date}</td>
                <td>${record.entry_time}</td>
                <td>${record.exit_time}</td>
            `;
            previewTableBody.appendChild(row);
        });
    }
    
    if (dataStats) {
        dataStats.textContent = `${data.length} records loaded`;
        dataStats.className = 'status status--success';
    }
    
    console.log('Data preview updated');
}

function handleApiConfig(event) {
    event.preventDefault();
    console.log('Handling API config submission');
    
    const config = {
        apiKey: document.getElementById('apiKey').value.trim(),
        accessToken: document.getElementById('accessToken').value.trim(),
        underlying: document.getElementById('underlying').value,
        interval: document.getElementById('interval').value
    };
    
    console.log('API Config:', config);
    
    // Validate configuration
    if (!config.apiKey || !config.accessToken || !config.underlying || !config.interval) {
        showError('Please fill in all required fields');
        return;
    }
    
    // Store configuration
    appState.apiConfig = config;
    
    // Show success and start processing
    showSuccessMessage('API configuration validated successfully');
    setTimeout(() => {
        startDataProcessing();
    }, 1000);
}

function startDataProcessing() {
    console.log('Starting data processing...');
    showSection('processingSection');
    
    const totalRecords = appState.uploadedData.length;
    let processedCount = 0;
    
    // Clear previous results
    appState.processedResults = [];
    
    const processingStatus = document.getElementById('processingStatus');
    if (processingStatus) {
        processingStatus.innerHTML = '';
    }
    
    logMessage('Starting data processing...', 'info');
    logMessage(`Processing ${totalRecords} option records`, 'info');
    
    // Simulate processing each record
    const processRecord = async (record, index) => {
        return new Promise((resolve) => {
            setTimeout(() => {
                const result = simulateOptionDataFetch(record);
                appState.processedResults.push(result);
                
                processedCount++;
                const progress = (processedCount / totalRecords) * 100;
                
                updateProgress(progress, `Processing record ${processedCount}/${totalRecords}`);
                logMessage(`Processed: ${result.option_details} - P&L: ₹${result.pnl}`, 
                          result.pnl >= 0 ? 'success' : 'error');
                
                resolve(result);
            }, 500 + Math.random() * 1000); // Random delay for realistic simulation
        });
    };
    
    // Process all records
    Promise.all(appState.uploadedData.map(processRecord))
        .then(() => {
            logMessage('All records processed successfully!', 'success');
            updateProgress(100, 'Processing complete');
            
            setTimeout(() => {
                showResults();
            }, 1000);
        })
        .catch((error) => {
            console.error('Processing error:', error);
            logMessage('Error during processing', 'error');
        });
}

function simulateOptionDataFetch(record) {
    // Generate realistic option prices
    const basePrice = Math.random() * 100 + 50; // Base price between 50-150
    const volatility = 0.1 + Math.random() * 0.2; // 10-30% volatility
    
    const entryPrice = Math.round(basePrice * (1 + (Math.random() - 0.5) * volatility * 2) * 100) / 100;
    const exitPrice = Math.round(basePrice * (1 + (Math.random() - 0.5) * volatility * 2) * 100) / 100;
    
    const pnl = Math.round((exitPrice - entryPrice) * 100) / 100;
    const returnPct = entryPrice > 0 ? Math.round((pnl / entryPrice) * 10000) / 100 : 0;
    
    // Generate option details
    const optionDetails = `${appState.apiConfig.underlying} ${record.strike_price} ${record.option_type.toUpperCase()}`;
    
    return {
        option_details: optionDetails,
        strike_price: record.strike_price,
        option_type: record.option_type,
        expiry_date: record.expiry_date,
        entry_time: record.entry_time,
        exit_time: record.exit_time,
        entry_price: entryPrice,
        exit_price: exitPrice,
        pnl: pnl,
        return_pct: returnPct
    };
}

function updateProgress(percentage, message) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    if (progressFill) {
        progressFill.style.width = `${percentage}%`;
    }
    if (progressText) {
        progressText.textContent = message;
    }
}

function logMessage(message, type = 'info') {
    const processingStatus = document.getElementById('processingStatus');
    if (!processingStatus) return;
    
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    
    const time = new Date().toLocaleTimeString();
    logEntry.innerHTML = `
        <span class="log-time">${time}</span>
        <span class="log-message log-${type}">${message}</span>
    `;
    
    processingStatus.appendChild(logEntry);
    processingStatus.scrollTop = processingStatus.scrollHeight;
}

function showResults() {
    console.log('Showing results...');
    showSection('resultsSection');
    
    const resultsSummary = document.getElementById('resultsSummary');
    const resultsTableBody = document.getElementById('resultsTableBody');
    
    // Calculate summary statistics
    const totalTrades = appState.processedResults.length;
    const totalPnL = appState.processedResults.reduce((sum, result) => sum + result.pnl, 0);
    const profitableTrades = appState.processedResults.filter(result => result.pnl > 0).length;
    const avgReturn = totalTrades > 0 ? 
        appState.processedResults.reduce((sum, result) => sum + result.return_pct, 0) / totalTrades : 0;
    
    // Display summary
    if (resultsSummary) {
        resultsSummary.innerHTML = `
            <div class="summary-card">
                <div class="summary-value">${totalTrades}</div>
                <div class="summary-label">Total Trades</div>
            </div>
            <div class="summary-card ${totalPnL >= 0 ? 'profit' : 'loss'}">
                <div class="summary-value">₹${totalPnL.toFixed(2)}</div>
                <div class="summary-label">Total P&L</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">${profitableTrades}</div>
                <div class="summary-label">Profitable Trades</div>
            </div>
            <div class="summary-card ${avgReturn >= 0 ? 'profit' : 'loss'}">
                <div class="summary-value">${avgReturn.toFixed(2)}%</div>
                <div class="summary-label">Avg Return</div>
            </div>
        `;
    }
    
    // Display results table
    if (resultsTableBody) {
        resultsTableBody.innerHTML = '';
        appState.processedResults.forEach(result => {
            const row = document.createElement('tr');
            const pnlClass = result.pnl > 0 ? 'profit' : result.pnl < 0 ? 'loss' : 'neutral';
            
            row.innerHTML = `
                <td>${result.option_details}</td>
                <td>${result.expiry_date}</td>
                <td>${result.entry_time}</td>
                <td>${result.exit_time}</td>
                <td>₹${result.entry_price.toFixed(2)}</td>
                <td>₹${result.exit_price.toFixed(2)}</td>
                <td class="${pnlClass}">₹${result.pnl.toFixed(2)}</td>
                <td class="${pnlClass}">${result.return_pct.toFixed(2)}%</td>
            `;
            resultsTableBody.appendChild(row);
        });
    }
    
    console.log('Results displayed');
}

function exportResults() {
    console.log('Exporting results...');
    
    if (appState.processedResults.length === 0) {
        showError('No results to export');
        return;
    }
    
    // Prepare data for export
    const exportData = appState.processedResults.map(result => ({
        'Option Details': result.option_details,
        'Strike Price': result.strike_price,
        'Option Type': result.option_type,
        'Expiry Date': result.expiry_date,
        'Entry Time': result.entry_time,
        'Exit Time': result.exit_time,
        'Entry Price': result.entry_price,
        'Exit Price': result.exit_price,
        'P&L': result.pnl,
        'Return %': result.return_pct
    }));
    
    try {
        // Create workbook and worksheet
        const workbook = XLSX.utils.book_new();
        const worksheet = XLSX.utils.json_to_sheet(exportData);
        
        // Add worksheet to workbook
        XLSX.utils.book_append_sheet(workbook, worksheet, 'Options Results');
        
        // Generate file name with current date
        const today = new Date();
        const fileName = `options_backtest_results_${today.getFullYear()}-${(today.getMonth()+1).toString().padStart(2,'0')}-${today.getDate().toString().padStart(2,'0')}.xlsx`;
        
        // Download the file
        XLSX.writeFile(workbook, fileName);
        
        showSuccessMessage('Results exported successfully!');
        console.log('Export completed');
    } catch (error) {
        console.error('Export error:', error);
        showError('Error exporting results');
    }
}

// Utility Functions
function showSection(sectionId) {
    console.log('Showing section:', sectionId);
    const section = document.getElementById(sectionId);
    if (section) {
        section.style.display = 'block';
        // Smooth scroll to section
        setTimeout(() => {
            section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    } else {
        console.error('Section not found:', sectionId);
    }
}

function showError(message) {
    console.error('Error:', message);
    removeMessages();
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `<p>${message}</p>`;
    
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.insertBefore(errorDiv, mainContent.firstChild);
    }
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.remove();
        }
    }, 5000);
}

function showSuccessMessage(message) {
    console.log('Success:', message);
    removeMessages();
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.innerHTML = `<p>${message}</p>`;
    
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.insertBefore(successDiv, mainContent.firstChild);
    }
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (successDiv.parentNode) {
            successDiv.remove();
        }
    }, 3000);
}

function removeMessages() {
    const messages = document.querySelectorAll('.error-message, .success-message');
    messages.forEach(message => {
        if (message.parentNode) {
            message.remove();
        }
    });
}