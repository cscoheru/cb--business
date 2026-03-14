// bright-data-amazon.js
/**
 * Bright Data Amazon Channel - Test Version
 *
 * Simple test to verify the channel works
 */

const BRIGHT_DATA_API = 'https://api.brightdata.com/datasets/v3/scrape';
const BRIGHT_DATA_TOKEN = '1c7806b0-3f98-48da-93ce-8a745c40b062';

async function testBrightDataAPI() {
    // Test with a simple Amazon product URL collection
    const payload = {
        input: [{
            url: 'https://www.amazon.com/Quencher-FlowState-Stainless-Insulated-Smoothie/dp/B0CRMZHDG8',
            zipcode: '94107',
            language: ''
        }]
    };

    const params = new URLSearchParams({
        dataset_id: 'gd_l7q7dkf244hwjntr0',
        notify: 'false',
        include_errors: 'true'
    });

    const url = `${BRIGHT_DATA_API}?${params}`;

    console.log('🧪 Testing Bright Data API...');
    console.log('URL:', url);

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${BRIGHT_DATA_TOKEN}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        console.log('✅ API Response successful');
        console.log('Results:', data.results ? data.results.length : 0);

        if (data.results && data.results.length > 0) {
            const products = data.results[0].content;
            console.log('Products:', products ? products.length : 0);

            if (products && products.length > 0) {
                console.log('Sample product:', JSON.stringify(products[0], null, 2).substring(0, 500));
            }
        }

        return {
            success: true,
            message: 'Bright Data API test successful',
            products_collected: data.results ? data.results.length : 0
        };

    } catch (error) {
        console.error('❌ Error:', error.message);
        return {
            success: false,
            error: error.message
        };
    }
}

module.exports = { main };
