
// TODO: rimosso per il momento il riferimento al CKEDITOR

var entityMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
    '/': '&#x2F;',
    '`': '&#x60;',
    '=': '&#x3D;'
};


function escapeHtml(string) {
    return String(string).replace(/[&<>"'`=\/]/g, function (s) {
        return entityMap[s];
    });
}

function load_to_textbox(url, el) {
    $.get(url, null, function (data) {
        el.val(data);
        $('#txt-popup').html(data);
    }, "text");

}

/**
 * imposta il timeout per la chiusura automatica degli alert
 *
 * @param id
 */
function setAlertTimeout(id) {
    setTimeout(function () {
        $(id).hide();
    }, 5000);
}

var textFile = null;

/**
 * Pulisce l'area di testo
 *
 * @constructor
 */
function PulisceArea() {
    var src_msg = 'Carica o incolla il testo da parsare...';
    $('#sorgente').val(src_msg);
    $('#txt-popup').html(src_msg);
    // Solo per l'elemento iniziale del DOM
    var tr_msg = 'Esegui la trasformazione...';
    var sel = $('#xml')
    sel.text(tr_msg)
    // fa il refresh dell'elemento corrente e non di quando il DOM è stato caricato
    sel.val(tr_msg)
    $('#xml-popup').html(tr_msg);
    $('#xml-popup-p').html(tr_msg);
    $('#akn-popup').html(tr_msg);
    $('#akn-popup-l').html(tr_msg);
    setDataIntoCkEditor(tr_msg);
}

function makeTextFile(text) {
    var data = new Blob([text], {type: 'text/xml'});

    // If we are replacing a previously generated file we need to
    // manually revoke the object URL to avoid memory leaks.
    if (textFile !== null) {
        window.URL.revokeObjectURL(textFile);
    }
    textFile = window.URL.createObjectURL(data);
    return textFile;
}

/**
 * Inserisce i dati nel CKEditor
 * @param data
 */
function setDataIntoCkEditor(data)
{

    <!-- CKEDITOR -->
    //console.log(CKEDITOR.instances.editor1)

    /*
    if (CKEDITOR.instances.editor1 === undefined) {
        //console.log("replace")
        CKEDITOR.replace( 'editor1', {  extraPlugins: 'xml' } );
    }

    CKEDITOR.instances.editor1.setData(data);
    */
}


/**
 * Funzioni e assegnazioni al ready del document
 */
$(document).ready(function () {

    /**
     * Funzione che richiama il trasformatore del file di testo in XML
     */
    $('#btn_trasforma').click(function () {
        $(this).prop('disabled', true);
        //$('#btn_trasforma').disable();
        $.ajax({
            url: 'rest/parse',
            //data: JSON.stringify($('form').serialize()),
            data: JSON.stringify({testo: $("textarea[name=testo]").val()}),
            contentType: "application/json; charset=utf-8",
            dataType: 'json',
            type: 'POST',
            success: function (response) {
                var xml = response['xml']
                var akn = response['akn']

                //console.log(akn);

                var xxml = escapeHtml(xml);
                var xakn = escapeHtml(akn);

                $('#xml').html(xxml);
                $('#xml-popup-p').html(xxml);
                // //setDataIntoCkEditor(response['xml']);
                // --------------------------
                $('#xml-popup').html("");
                $('#xml-popup').show();
                new XMLTree({
                    xml : vkbeautify.xml(xml).trim(),
                    container : '#xml-popup',
                    startExpanded : true,
                    noDots: true
                });
                // --------------------------

                $('#akn-popup-l').html(xakn);

                // --------------------------
                $('#akn-popup').html("");
                $('#akn-popup').show();
                if (akn.trim().length>0 && akn[0]!=='@') {
                    new XMLTree({
                        xml: vkbeautify.xml(akn).trim(),
                        container: '#akn-popup',
                        startExpanded: true,
                        noDots: true
                    });
                }
                else
                {
                    if (akn[0]!=='@')
                        alert("Errore di conversione AKN!");
                }
                // --------------------------

                // Imposta i link

                var link_xml = document.getElementById('downloadlink');
                link_xml.href = makeTextFile(response['xml']);

                var link_xml = document.getElementById('downloadlink-xmlp');
                link_xml.href = makeTextFile(response['xml']);

                var link_akn = document.getElementById('downloadlink-akn');
                link_akn.href = makeTextFile(response['akn']);

                //$('pre code').each(function (i, block) {

                // Effettua l'highlight del box #xml
                $('pre code#xml').each(function (i, block) {
                    hljs.highlightBlock(block);
                });
                // Effettua l'highlight del box #xml-popup-p
                $('pre code#xml-popup-p').each(function (i, block) {
                    hljs.highlightBlock(block);
                });

                // Effettua l'highlight del box #akn-popup-l
                $('pre code#akn-popup-l').each(function (i, block) {
                    hljs.highlightBlock(block);
                });

                $("#stderr").text(response['stderr']);

                $('#parse_alert').show();
                setAlertTimeout('#parse_alert');
                //console.log($(this));
                $('#btn_trasforma').prop('disabled', false);
            },
            error: function (error) {
                $('#parse_alert_ko').show();
                setAlertTimeout('#parse_alert_ko');
                $('#btn_trasforma').prop('disabled', false);
            }
        });
    });

    /**
     * Carica il testo selezionato nella ListBox
     */
    $('#btn_carica').click(function () {
        var text = $("#samples option:selected").text();
        load_to_textbox("res/txt/" + text, $('#sorgente'));
        $('#carica_alert').show();
        setAlertTimeout('#carica_alert');

    });

    /**
     * Pulisce l'area di testo
     */
    $('#btn_pulisce').click(function () {
        new PulisceArea();
    });

    /**
     * Chiude gli alert
     */
    $(".close").click(function () {
        $('.alert').hide()
    });

    /**
     * Carica i file di testo di esempio nella Listbox
     */
    $.getJSON("rest/samples", function (data) {
        $.each(data, function (index, item) {
            for (var i in item) {
                $('#samples').append($('<option></option>').val(i).html(item[i]));
            }
        });
    });


    //CKEDITOR.plugins.addExternal( 'xml', '/res/js/ckeditor/plugins/xml/', 'plugin.js' );

    /**
     * La prima cosa che fa è cancellare l'Area di Testo
     */
    new PulisceArea();
});


