document.addEventListener('DOMContentLoaded', function() {
    
    const phoneForm = document.getElementById('phone-form');
    if (phoneForm) {
        // A minimal list of countries for demonstration
        const countries = [
            { name: 'India', code: '91', iso: 'IN' }, 
            { name: 'United States', code: '1', iso: 'US' }, 
            { name: 'United Kingdom', code: '44', iso: 'GB' },
            { name: 'Afghanistan', code: '93', iso: 'AF' }, 
            { name: 'Albania', code: '355', iso: 'AL' },
            { name: 'Germany', code: '49', iso: 'DE' },
            { name: 'France', code: '33', iso: 'FR' },
            { name: 'Canada', code: '1', iso: 'CA' }
        ];

        const container = document.querySelector('.custom-select-container');
        const selected = container.querySelector('.select-selected');
        const items = container.querySelector('.select-items');
        const countryCodeSpan = document.getElementById('country-code');
        const fullPhoneNumberInput = document.getElementById('full-phone-number');
        const phoneNumberOnlyInput = document.getElementById('phone-number-input');

        countries.forEach(country => {
            const option = document.createElement('div');
            option.classList.add('select-option');
            option.innerHTML = `
                <div class="country-info">
                    <span class="iso">${country.iso}</span>
                    <span class="name">${country.name}</span>
                </div>
                <span class="code">+${country.code}</span>
            `;
            option.addEventListener('click', (e) => {
                e.stopPropagation();
                selected.innerHTML = `
                    <div class="country-info">
                        <span class="iso">${country.iso}</span>
                        <span class="name">${country.name}</span>
                    </div>`;
                countryCodeSpan.textContent = `+${country.code}`;
                updatePhoneNumber();
                items.classList.add('select-hide');
                selected.classList.remove('select-arrow-active');
            });
            items.appendChild(option);
        });

        const initialCountry = countries[0];
        selected.innerHTML = `
            <div class="country-info">
                <span class="iso">${initialCountry.iso}</span>
                <span class="name">${initialCountry.name}</span>
            </div>`;
        
        selected.addEventListener('click', (e) => {
            e.stopPropagation();
            items.classList.toggle('select-hide');
            selected.classList.toggle('select-arrow-active');
        });

        const updatePhoneNumber = () => {
            fullPhoneNumberInput.value = countryCodeSpan.textContent.replace(/\s/g, '') + phoneNumberOnlyInput.value.replace(/\s/g, '');
        };

        phoneNumberOnlyInput.addEventListener('input', updatePhoneNumber);
        updatePhoneNumber();

        document.addEventListener('click', () => {
            items.classList.add('select-hide');
            selected.classList.remove('select-arrow-active');
        });
    }
});