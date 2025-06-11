//Import tagify objects for event listeners
import { fieldTagify, softwareTagify,
        initTagify, fieldInWhitelist, softwareInWhitelist } from "./tags.js";

import {header, siteMenus, footer, footerMenus, universalMenus} from "https://esm.sh/@access-ci/ui@0.8.0"

import { showAlert } from './alerts.js';

const siteItems =[
    {
        name: "Software Documentation Service",
        href: "https://access-sds.ccs.uky.edu:8080/"
    },
    {
        name: "Events & Training",
        href: "https://support.access-ci.org/events"
    },
    {
        name: "Resources",
        href: "https://allocations.access-ci.org/resources"
    },
    {
        name: "Prepare Requests",
        href: "https://allocations.access-ci.org/prepare-requests"
    },
    {
        name: "Exchange Credits",
        href: "https://allocations.access-ci.org/exchange_calculator"
    }
]

var { addFieldTagify, addSoftwareTagify } = initTagify()

// Enable all bootstrap tooltips
var tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
var tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))


$(document).ready(function(){
    $('html,body').animate({scrollTop:0},'fast')

    universalMenus({
        loginUrl: "/login",
        logoutUrl: "/logout",
        siteName: "Allocations",
        target: document.getElementById("universal-menus"),
    });
    header({
        siteName: "Support",
        target: document.getElementById("header")
    });
    siteMenus({
        items: siteItems,
        siteName: "Allocations",
        target: document.getElementById("site-menus"),
      });

    footerMenus({
        items: siteItems,
        siteName: "Support",
        target: document.getElementById("footer-menus"),
    });
    footer({ target: document.getElementById("footer") });

    const shadowHost = document.getElementById('universal-menus');
    const shadowRoot = shadowHost.shadowRoot;
    const loginButton = shadowRoot.querySelector('li:last-child button');
    loginButton.remove();

    //event listeners for tagify fields
    addFieldTagify.on("invalid", fieldInWhitelist)

    addSoftwareTagify.on("invalid", softwareInWhitelist);

    //initialize tooltips
    $('[data-toggle="tooltip"]').tooltip()

    var formDataObject = {};
    var recommendationObj;
    var recommendedResources;
    $("#submit-form").on("click", function(e){
        // calculate scores when the form is submitted
        e.preventDefault();
        var form = document.getElementById("recommendation-form")
        let formData = get_form_data(form);
        calculate_score(formData).then(function(recommenadtion) {
            recommendationObj = JSON.parse(recommenadtion)
            recommendedResources = getRecommendedResources(recommendationObj);
            if (!(Object.keys(recommendedResources).length === 0)){
                // Creates the accordions for the top 3 (or fewer) recommendations in the modal
                visualize_recommendations(recommendedResources, Math.min(3, Object.keys(recommendedResources).length));
                $("#submitModal").modal("show");
                $("#see_less").hide()
                $("#see_more").show()
                // Saves the form data so that it can be used in the "See More" button below.
                formDataObject = formData
            }else{
                let alertMsg = "Not enough information to make recommendation. Please provide a more detailed response"
                showAlert(alertMsg, 'danger')
            }
            show_xdmod_data();

        });

        return false
    })

    //add three more calculated scores when see more button is clicked
    $('#see_more').on('click', function(){

        // Reads the number of recommendations in the modal to only load the subsequent three
        let numberOfAccordions = $("#submitModalBody .accordion-item").length;
        let numRecs = Object.keys(recommendedResources).length
        let newAccordions = Math.min(numRecs, numberOfAccordions + 3);

        // Makes the next set of  boxes/recommendations and adds to the modal
        visualize_recommendations(recommendedResources, newAccordions)
        .then(() => {

            // Hide the "See More" button and show the "See Less" when all recommendations have been displayed
            if (newAccordions >= numRecs){
                $("#see_more").hide();
                $("#see_less").show();
            }

            show_xdmod_data();

        })
        .catch((error) => {
            console.error("Error occurred: " + error);
        });
    });

    // Reduce the recommendations back down to the top three
    $('#see_less').on('click', function(){
        // Clears the accordion
        document.querySelector('#recommendation-accordion').innerHTML = '';
        //Calculates the top three and displays them in the modal
        visualize_recommendations(recommendedResources, Math.min(3, Object.keys(recommendedResources).length)).then( () => {
            $("#see_more").show()
            $("#see_less").hide()
            show_xdmod_data();
        })
        .catch((error) => {
            console.error("Error occured when trying to show fewer recommendations: ", error);
        })
    })

    $("#submitModal").on('hidden.bs.modal', function() {
        // make sure the recommendations are empty
        $("#recommendation-accordion").empty()
    })

    //Show RPs if user has experience
    $('input[name="hpc-use"]').change(function() {
        if ($(this).val() === '1') {
          $('.hide-hpc').removeClass('d-none').show();
        } else {
          $('.hide-hpc').addClass('d-none').hide();
        }
      });

    //Show GUI checkboxes if user needs GUI
    $('input[name="gui-needed"]').change(function(){
        if ($(this).val() === '1'){
            $('.hide-gui').removeClass('d-none').show();
        } else {
            $('.hide-gui').addClass('d-none').hide();
        }
    });

    //Show storage questions if user needs storage
    $('input[name="storage"]').change(function() {
        if ($(this).val() === '1') {
          $('.hide-data').removeClass('d-none').show();
        } else if ($(this).val() === '2') {
           $('.hide-data').removeClass('d-none').show();
        } else {
            $('.hide-data').addClass('d-none').hide();
        }
      });

    //Show gpu questions if user needs gpus
    $('input[name="gpu"]').change(function() {
        if ($(this).val() === '1') {
            $('.hide-gpu').removeClass('d-none').show();
        } else if ($(this).val() === '2') {
            $('.hide-gpu').removeClass('d-none').show();
        } else {
            $('.hide-gpu').addClass('d-none').hide();
        }
        });

    // Clear the form
    $("#clear-form").on('click',function(){
        let form = document.getElementById("recommendation-form");
        form.reset();
        // Hide all expanded items
        $('*[class*="hide-"]').addClass('d-none').hide();

    });

});

async function get_xdmod_data(){
    return new Promise(function(resolve,reject){
        $.ajax({
            type:"POST",
            url:"/get_xdmod_data",
            contentType:"application/json",
            success:function(recommendation){
                resolve(recommendation)
            },
            error:function(error){
                reject(error)
            }
        });
    });
}

function convert_hours(hours){
    // Convert to days if 24 or more hours
    if (hours >= 24) {
        const days = Math.round(hours / 24 * 100) / 100; // Maintain 2 decimal places
        return days === 1 ? "1 day" : `${days} days`;
    }

    // Convert to minutes if less than 1 hour
    if (hours < 1) {
        const minutes = Math.round(hours * 60);
        return minutes === 1 ? "1 min." : `${minutes} mins.`;
    }

    // Keep as hours otherwise
    return hours === 1 ? "1 hour" : `${hours} hrs.`;
}

var xdmodData;
function show_xdmod_data(){
    // Create and return a Promise (to avoid turning everything into async)
    const dataPromise = (typeof xdmodData === 'undefined')
        ? get_xdmod_data().then(data => { xdmodData = JSON.parse(data); })
        : Promise.resolve();
    dataPromise.then(() => {
        const accordionItems = $(".accordion-item");
        let xdmodResources  = Object.keys(xdmodData)
        accordionItems.each(function() {
            const id = $(this).attr("id");
            if (id) {
                let resource = id.split('-').slice(0,-1)
                if (resource.length > 1) {
                    resource = resource.join("-")
                } else {
                    resource = resource[0]
                }

                let time;
                if (resource === 'Anvil') {
                    time = `Anvil CPU: ${convert_hours(xdmodData['Anvil_CPU'])}`
                    time = time.concat(`, Anvil GPU: ${convert_hours(xdmodData['Anvil_GPU'])}`)
                } else {
                    time = convert_hours(xdmodData[resource]);
                }

                if (xdmodResources.includes(resource) && $(`#${resource}-accordion-button`).has('.xdmod-data').length == 0){
                    $(`#${resource}-accordion-button`).append(`
                        <span
                            class="xdmod-data"
                            data-bs-toggle="tooltip"
                            data-bs-title="Average time jobs spend in queue before starting to run (past 30 days): ${time}"
                        >
                            <i class="icon bi bi-hourglass-split"></i>
                        </span>
                    `)
                }

                // Add time specifically for ANVIL CPU and GPU resources.
                if ((resource === 'Anvil') && (xdmodResources.includes('Anvil_CPU') && $(`#${resource}-accordion-button`).has('.xdmod-data').length == 0)) {
                    console.log(resource)
                    $(`#${resource}-accordion-button`).append(`
                        <span
                            class="xdmod-data"
                            data-bs-toggle="tooltip"
                            data-bs-title="Average time jobs spend in queue before starting to run (past 30 days): ${time}"
                        >
                            <i class="icon bi bi-hourglass-split"></i>
                        </span>
                    `)
                }
            }
        });
        // enable newly created tooltips
        tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
        tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

    }).catch(error => {
        console.error("Unable to find xdmod data:", error);
    });
}

function get_form_data(form){
    let formData = new FormData(form)

    //Set research field tags and added tags
    let fieldTagValues = fieldTagify.value.map(tag => tag.value)
    formData.set('research-field', fieldTagValues)

    //Set software tags and added tags
    let softwareTagValues = softwareTagify.value.map(tag => tag.value)
    formData.set('software', softwareTagValues)

    return formData
}

function calculate_score(formData){

    // get and process data from each input field
    let jsonData = {}
    formData.forEach(function(value,key){
        if (key == "used-hpc" || key == "used-gui" || key == "gpus" || key == "gpus_ram"){
            if (!jsonData[key]) {
                jsonData[key] = [value];
            } else {
                jsonData[key].push(value);
            }
        } else {
            jsonData[key]=value
        }
    });

    //calculating score from backend
    return new Promise(function(resolve,reject){
        $.ajax({
            type:"POST",
            url:"/get_score",
            data:JSON.stringify(jsonData),
            contentType:"application/json",
            success:function(recommendation){
                resolve(recommendation)
            },
            error:function(error){
                reject(error)
            }
        });
    });

}

function getRecommendedResources(recommenadtionObj, threshold = 1) {
    // returns only the objects that have a score (i.e. are recommended)
    return Object.fromEntries(
      Object.entries(recommenadtionObj)
        .filter(([_, value]) => value.score >= threshold)
    );
}

async function addAccordion(recommendation) {
    const display_name = recommendation.name
    let resource;
    if (display_name.includes(" ")) {
        resource = display_name.replaceAll(" ","-");
    } else {
        resource = display_name
    }
    let recommendation_accordion = $("#recommendation-accordion");
    let recommendation_reasons = "";

    // let reason = recommendations[i].reasons;
    if (recommendation.reasons) {
        recommendation.reasons.forEach((r) => {
            recommendation_reasons += `
                <span class="reason badge">
                    ${r}
                </span>
            `;
        })
    }

    let accordion_item = `
        <div class="accordion-item border-0" id="${resource}-accordion">
        <h2 class="accordion-header" id="${resource}-header">
            <button class="accordion-button collapsed justify-content-between d-flex" type="button" data-bs-toggle="collapse"
            data-bs-target="#${resource}-collapse" aria-expanded="false"
            aria-controls="${resource}-collapse">
                <div class="d-flex justify-content-between w-100" id="${resource}-accordion-button">
                    <strong flex-grow-1>${display_name}</strong>
                </div>
            </button>
        </h2>
        <div id="${resource}-collapse" class="accordion-collapse collapse"
            aria-labelledby="${resource}-header">
            <div class="accordion-body">
            <div id='${resource}-content'>
                <div class="reasons-container" id="${resource}-reasons">
                    ${recommendation_reasons}
                </div>
                <div class="body-container" id="${resource}-body"></div>
            </div>
            </div>
        </div>
        </div>
    `;

    recommendation_accordion.append(accordion_item);

    //Generates blurbs and links for each RP by pulling from database
    try {
        // Make the AJAX request to info/blurb database using fetch API and await the response
        const jsonData = { rp: recommendation.name };
        const response = await $.ajax({
            type: "POST",
            url: '/get_info',
            data: JSON.stringify(jsonData),
            contentType: "application/json",
            error:function(error){
                reject(error)
            }
        });
        // takes the JSON response and uses it to add the blurbs and links into the recommendations boxes
        const info = await response;
        const bodyContainer = document.getElementById(`${resource}-body`);
        if (bodyContainer) {
            const blurbArray = info.blurb;
            const hyperlinkArray = info.hyperlink;
            const documentationArray = info.documentation;
            const index = info.rp.indexOf(recommendation.name);
            bodyContainer.innerHTML = bodyContainer.innerHTML + `
                <p class="blurb">${blurbArray[index]}</p>
                <a href="${hyperlinkArray[index]}" target="_blank">Resource Page</a>
                <a href="${documentationArray[index]}" target="_blank">Documentation</a>
            `;
        }
      } catch (error) {
        // Handle any other errors that might occur during the AJAX request
        console.error("Error fetching RP information:", error);
      }
}

//function to parse JSON data a create a boxes in the modal to display them
async function visualize_recommendations(scores, recNum){
    // parses JSON data from calculate scores function
    var recommendations=[];
    //Creates a variable recommendations that houses the parsed JSON data
    for (let rp in scores) {
        if (scores.hasOwnProperty(rp)) {
            var score = scores[rp]['score'];
            var reasons = scores[rp]['reasons'];
            recommendations.push({ name: rp, score: score, reasons: reasons });
        }
    }
    // sorts the recommendations from high to low scores
    recommendations.sort(function(a, b) {
        return b.score - a.score;
    });
    // takes recNum argument to make params that only display a certain section of recommendations. Used for "See More" button
    var high = recNum
    for (let i=0; i<(high); i++){

        let resource = recommendations[i].name;
        let accordion_item = $(`#${resource}-accordion`);

        // If the recommenadtion item already exists then skip it
        if (accordion_item.length > 0) {
            continue;
        }
        addAccordion(recommendations[i])
    }

}
