$(document).ready(function() {

  // Update default value start-date
  var today = new Date().toISOString().substr(0, 10);
  document.querySelector("#start-date").value = today;

  // $('.multiselect').multiselect();

  $(".multiselect").multiselect({
    includeSelectAllOption: true,
    maxHeight: 200,
  });

  var paginationTop = $('#pagination-top');
  var paginationBottom = $('#pagination-bottom');
  paginationTop.hide();
  paginationBottom.hide();

  // Check if there are any stored values in local storage
  if (localStorage.getItem('searchFormData')) {
    // Retrieve the stored values and parse them as a JSON object
    const searchFormData = JSON.parse(localStorage.getItem('searchFormData'));

    // Loop through the form fields and set their values to the stored values
    for (const field in searchFormData) {
      const element = document.querySelector(`[name="${field}"]`);
      if (element) {
        if (element.type === 'select-multiple') {
          // Check if default selected should be removed
          let removeSelectedAll = false;
          for (const option of element.options) {
            if (searchFormData[field].includes(option.value)) {
              removeSelectedAll = true;
            }
          }
          for (const option of element.options) {
            if (removeSelectedAll === true) {
              option.selected = false;
            }
          }
          $(`select[name="${field}"]`).multiselect('refresh');
          // For select fields, loop through the options and set the selected attribute
          for (const option of element.options) {
            if (searchFormData[field].includes(option.value)) {
              option.selected = true;
              // const button = document.querySelector(`button[title="${option.text}"]`);
              // button.classList.add("active");
              // const input = button.querySelector('input[type="checkbox"]');
              // input.checked = true;
              $(`select[name="${field}"]`).multiselect('refresh');
            }
          }
        } else {
          // For other fields, set the value attribute
          element.value = searchFormData[field];
        }
      }
    }
  }
  // Listen for a form submission
  $('#search-tournaments').on('submit', (event) => {
    // Prevent the default form submission behavior
    event.preventDefault();

    // Get the form data as a JSON object
    const formData = {};
    // Loop through all form elements
    $('form :input').each(function() {
      const element = $(this);
      if (element.attr('name')) {
        if (element.is('select[multiple]')) {
          // For select fields, loop through the options and add their values to an array
          const selectedOptions = [];
          $('option:selected', element).each(function() {
            selectedOptions.push($(this).val());
          });
          formData[element.attr('name')] = selectedOptions;
        } else {
          // For other fields, add the value to the JSON object
          formData[element.attr('name')] = element.val();
        }
      }
    });
    localStorage.setItem('searchFormData', JSON.stringify(formData));

    // Get the form data and convert it to a JSON string
    var formDataJson = JSON.stringify($(event.currentTarget).serializeArray());

    // Make the AJAX request
    var apiKey = "AIzaSyBKvYYdqetSVRFVCoY0HIwteFjVGfE1AeM";

    // Get the #results div
    const resultsDiv = $('#results');
    resultsDiv.html('');
    paginationTop.html('');
    paginationBottom.html('');
    const pageSize = 6;

    $.ajax({
      type: 'POST',
      url: '/api/search',
      data: formDataJson,
      contentType: 'application/json',
      success: function(response) {
        // Handle the successful response here
        console.log(response);

        const totalItems = response['hydra:totalItems'];
        const totalPages = Math.ceil(totalItems / pageSize);

        // Alternatively, you can use the .forEach() method:
        let elemList = [paginationTop, paginationBottom];
        let pageValue = $('input[name="page"]:last').val();
        if (pageValue === undefined) {
          pageValue = 1
        }
        $(elemList).each(function(index, element) {
           var html = '';
           for (var i = 1; i <= totalPages; i++) {
              var active = (i == pageValue) ? 'active' : ''; // Add 'active' class to first item
              html += '<li class="page-item ' + active + '"><a class="page-link" data-page="' + i + '">' + i + '</a></li>';
           }

           // Add the HTML to the current element
           $(element).append(html);

           // Add click event listener to each page item
           $(element).find('.page-link').on('click', function(event) {
              event.preventDefault();
              var page = $(this).data('page');
              $('form').append('<input type="hidden" name="page" value="' + page + '">');
              $('form').submit();
           });

           element.show();
        });

        // Get user's origin location from localStorage
        const origin = formData['location'];
        // Loop through the hydra:member list
        response['hydra:member'].forEach(function(item) {
          // Get user's destination location from item
          let destination = ''
          if (item.address.streetAddress != null) {
            destination += item.address.streetAddress + ', '
          }
          if (item.address.postalCode != null) {
            destination += item.address.postalCode + ', '
          }
          if (item.address.addressLocality != null) {
            destination += item.address.addressLocality + ', '
          }
          if (item.address.addressRegion  != null) {
            destination += item.address.addressRegion
          }
          // const destination = item.address.streetAddress + ' ' + item.address.postalCode;
          // Create Google Maps Directions API URL
          const mapsUrl = "https://www.google.com/maps/embed/v1/directions?key=" + apiKey + "&origin=" + encodeURIComponent(origin) + "&destination=" + encodeURIComponent(destination) + "&mode=driving";

          // Add the iframe and horizontal line to the results div
          const row = $('<div>').addClass('row');
          const col1 = $('<div>').addClass('col-sm-5');
          const card = $('<div>').addClass('card');
          const cardBody = $('<div>').addClass('card-body');
          const title = $('<h5>').addClass('card-title').text(item.name);
          const clubName = $('<p>').addClass('card-text').text(item.club.name);

          let startDate = new Date(item.startDate)
          let formattedStartDate = startDate.getFullYear() + '-' + (startDate.getMonth() + 1).toString().padStart(2, '0') + '-' + startDate.getDate().toString().padStart(2, '0')
          let endDate = new Date(item.endDate)
          let formattedEndDate = endDate.getFullYear() + '-' + (endDate.getMonth() + 1).toString().padStart(2, '0') + '-' + endDate.getDate().toString().padStart(2, '0')
          const dateRange = $('<p>').addClass('card-text').text('Dates: ' + formattedStartDate + ' - ' + formattedEndDate);

          const address = $('<p>').addClass('card-text').text(destination);
          const contact = $('<p>').addClass('card-text').text('Organisateur: ' + item.contacts[0].givenName + ' ' + item.contacts[0].familyName);
          const email = $('<p>').addClass('card-text').text('Contact: ' + item.contacts[0].email);
          const rule = $('<p class="card-text">Règlement: <a style="text-decoration: underline" href="' + item.rules.url + '">Afficher le règlement</a></p>')

          const card2 = $('<div>').addClass('card');
          const cardBody2 = $('<div>').addClass('card-body');
          // const title2 = $('<h5>').addClass('card-title').text('New Card Title');
          // const description2 = $('<p>').addClass('card-text').text('New Card Description');

          let content2_html = '<p class="card-text">';
          if (item.tables.length > 0) {
            let tableDate = new Date(item.tables[0].date);
            var formattedTableDateHead = tableDate.getFullYear() + '-' + (tableDate.getMonth() + 1).toString().padStart(2, '0') + '-' + tableDate.getDate().toString().padStart(2, '0')
            content2_html += '<ul aria-label="">'
          } else {
            var formattedTableDateHead = ''
            content2_html += '<ul>'
          }

          item.tables.forEach(function(table) {
              let tableDate = new Date(table.date);
              formattedTableDate = tableDate.getFullYear() + '-' + (tableDate.getMonth() + 1).toString().padStart(2, '0') + '-' + tableDate.getDate().toString().padStart(2, '0')

              if (formattedTableDate != formattedTableDateHead) {
                formattedTableDateHead = formattedTableDate;
                content2_html += '</ul><ul aria-label="">';
              }
              content2_html += '<li>'
              if (table.name != null) {
                content2_html += table.name
              }
              if (table.description != null) {
                content2_html += ' - ' + table.description
              }
              if (table.time != null) {
                content2_html += ' - ' + table.time
              }
              if (table.fee != null) {
                content2_html += ' (' + table.fee/100 + '€)'
              }
              content2_html += '</li>';
          });
          content2_html += '</ul></p>'
          const content2 = content2_html;
          // https://apiv2.fftt.com/api/files/181948/Re%CC%81glement%20Tournoi%202023.pdf

          const col2 = $('<div>').addClass('col-sm-7');

          // Create the iframe for the Google Maps directions
          const iframe = $('<iframe>', {
            src: mapsUrl,
            frameborder: 0,
            // height: 450,
            // width: 600
            width: '100%',
            height: 450,
          });

          cardBody.append(title, clubName, dateRange, address, contact, email, rule);
          // cardBody2.append(title2, description2);
          cardBody2.append(content2);
          card.append(cardBody);
          card2.append(cardBody2);
          col1.append(card, card2);
          col2.append(iframe);
          row.append(col1, col2);

          resultsDiv.append(row, '<hr>');

        });
      },
      error: function(xhr, status, error) {
        // Handle the error here
      }
    });
  });
});
