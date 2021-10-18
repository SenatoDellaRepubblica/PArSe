<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0/CSD03"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:an="http://docs.oasis-open.org/legaldocml/ns/akn/3.0/CSD03"
    xmlns:bgt="http://www.senato.it/static/xml/def/1.0/bgt.html"
    xmlns:a="http://www.senato.it/static/xml/def/1.0/articolato.html"
    xmlns:cm="http://www.senato.it/static/xml/def/1.0/common.html"
    xmlns:dl="http://www.senato.it/static/xml/def/1.0/ddl.html"
    xmlns:em="http://www.senato.it/static/xml/def/1.0/emend.html"
    xmlns:h="http://www.w3.org/1999/xhtml" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    exclude-result-prefixes="xs xsi bgt a cm dl em h" version="2.0">
    <!--
        XSLT per trasformare gli articolati senato in formato XML Akoma Ntoso
        Versione 0.0.2 del 08/02/2013
        Versione 0.0.3 del 04/03/2013 - correzione namespace akoma 3.0
        Versione 0.1.0 del 06/06/2013 - completamento identificazione, inserimento evento generazione
        Versione 0.1.1 del 11/06/2013 - gestione delle references intradocumento per gli allegati e completamento della gestione degli annessi
        Versione 0.1.2 del 12/06/2013 - gestione delle url per le immagini
        Versione 0.1.3 del 01/10/2013 - corretti alcuni errori sull'html
        Versione 1.0.0 del 31/03/2014 - corretta la gestione del component info per le immagini
        Versione 1.0.1 del 27/06/2014 - estesa la gestione di nome e cognome per i presentatori
        Versione 1.0.2 del 19/06/2015 - corretta l'estrazione del numero stampato con la scelta del primo discendente
        Versione 1.0.3 del 26/07/2016 - inserita la gestione del preambolo nel frontespizio
        Versione 1.1.0 del 21/10/2016 - correzione bug nella gestione del numero particella
        
        
        TODO:
        - completare la gestione dell'ontologia, attualmente allo stato sommario
        - completare il workflow (se occorre. Al momento vengono inserite le varie fasi con data, tipo fase e numero stampato)
        
        DONE:
        - completate le voci dell'identificazione
        - completata la trasformazione della struttura dell'articolato
        - completata la gestione degli annessi con relative references
        - la coverPage dovrebbe essere completa
        - inserita la gestione del cm:Nota
        - creato il contenitore per il DecretoLegge (come act)
    -->

    <!-- variabili globali -->
    
    <!-- url alle ontologie -->
    <xsl:variable name="baseUriForOntologySenato" as="xs:string"
        >http://dati.senato.it/osr/</xsl:variable>
    <xsl:variable name="baseUriForOntologyCamera" as="xs:string"
        >http://dati.camera.it/ocd/</xsl:variable>
    
    <!-- metadati estratti dalla proprietà -->
    <xsl:variable name="docNumber" as="xs:string">
        <xsl:value-of select="/bgt:BGTDOC/dl:*[1]/dl:Proprieta[1]/dl:Protocollo[1]/@numero"/>
    </xsl:variable>
    <xsl:variable name="idTesto" as="xs:integer">
        <xsl:value-of select="number(/bgt:BGTDOC/dl:*[1]/dl:Proprieta[1]/dl:Protocollo[1]/@idTesto)"/>
    </xsl:variable>
    <xsl:variable name="legislatura" as="xs:string">
        <xsl:value-of select="/bgt:BGTDOC/dl:*[1]/dl:Proprieta[1]/dl:Protocollo[1]/@legislatura"/>
    </xsl:variable>
    <xsl:variable name="docDate" as="xs:string">
        <xsl:value-of select="/bgt:BGTDOC/dl:*[1]/dl:Proprieta[1]/dl:Protocollo[1]/@data"/>
    </xsl:variable>
    
    <xsl:variable name="placeholder" as="xs:string" select="'___'"/>
    
    <!-- tipo documento secondo BGT -->
    <xsl:variable name="tipoDoc" select="local-name(/bgt:BGTDOC/dl:*[1])"></xsl:variable>
    
    <!-- lista delle URI -->
    <!-- /it/Ddl/2013-05-02/588/ -->
    <xsl:variable name="URIWork" as="xs:string">
        <xsl:value-of select="concat( $baseUriForOntologySenato, 'Ddl/', $docDate, '/', $docNumber)"/>
    </xsl:variable>
    <!-- /it/Ddl/2013-05-02/588/ita@main -->
    <xsl:variable name="URIExpression" as="xs:string">
        <xsl:value-of select="concat( $URIWork, '/ita@')"/>
    </xsl:variable> 
    <!-- /it/Ddl/2013-05-02/588/ita@main.xml -->
    <xsl:variable name="URIManifestation" as="xs:string">
        <xsl:value-of select="concat( $URIExpression, '.akn' )"/>
    </xsl:variable> 
    
    <!-- url assoluta alle immagini  -->
    <xsl:variable name="urlImmagini" select="concat('http://www.senato.it/japp/bgt/showdoc/', $legislatura, '/', $tipoDoc, '/', format-number($idTesto,'00000000') , '/')" />

    <!-- deocodifica del tipo documento -->
    <xsl:variable name="descrizioneTipoDoc">
        <xsl:choose>
            <xsl:when test="$tipoDoc='DDLPRES'"><xsl:text>disegno di legge</xsl:text></xsl:when>
            <xsl:when test="$tipoDoc='DDLCOMM'"><xsl:text>relazione</xsl:text></xsl:when>
            <xsl:when test="$tipoDoc='DDLMESS'"><xsl:text>messaggio</xsl:text></xsl:when>
            <xsl:otherwise>altro</xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    
    <!-- entry point degli allegati -->
    <xsl:variable name="listaAllegati" 
        select="/bgt:BGTDOC/dl:*[1]/(dl:RelPres | dl:RelPres | dl:RelTec | dl:RelTecTabelle | dl:RelTecAllegati | dl:ParereCommissione | dl:AnalisiTecnicoNormativa | dl:DecretoLegge | dl:Allegato | dl:Altro[normalize-space(.)!='IL PRESIDENTE'] | a:Articolato[count(preceding-sibling::a:Articolato)>0])" />

    <!-- liste
        <xsl:key name="listaPersone" match="//dl:Presentatore/@nome" use="."/>
    <xsl:key name="listaPersone" match="//dl:Presentatore/@cognome" use="."/>
<xsl:key name="listaPersone" match="//dl:Presentatore[@cognome or @nome]" use="concat(@nome,'.', @cognome)"/>
    -->
    <xsl:key name="listaPersone" match="//dl:Presentatore[@cognome!='' or @nome!='']" use="normalize-space(concat(@nome, ' ', @cognome))"/>
    <xsl:key name="listaIncarichi" match="//dl:Presentatore/@incarico" use="."/>

    <!-- 
                ================================================ ENTRY POINT ================================================

        
        entry point, conversione da DDLPRES senato ad Akoma  -->
    <xsl:template match="/">
        <xsl:element name="an:akomaNtoso">
            <xsl:namespace name="an">http://docs.oasis-open.org/legaldocml/ns/akn/3.0/CSD03</xsl:namespace>
            <xsl:namespace name="xsi">http://www.w3.org/2001/XMLSchema-instance</xsl:namespace>
            <xsl:attribute name="schemaLocation"
                namespace="http://www.w3.org/2001/XMLSchema-instance">http://docs.oasis-open.org/legaldocml/ns/akn/3.0/CSD03 ../../Akoma/3.0/akomantoso30.xsd</xsl:attribute>
            <xsl:apply-templates select="/bgt:BGTDOC/dl:*[1]"/>
        </xsl:element>
    </xsl:template>

    <!-- 
        elemento radice del DDLPRES/DDLCOMM/DDLMESS che corrisponde all'elemento bill di akoma       
        L'ontologia del senato della repubblica ha namespace URI http://dati.senato.it/osr/
    -->
    <xsl:template match="dl:DDLPRES | dl:DDLCOMM | dl:DDLMESS">
        <xsl:element name="an:bill">
            <xsl:attribute name="contains">originalVersion</xsl:attribute>
            <xsl:element name="an:meta">
                <xsl:call-template name="crea.identification.Main"><xsl:with-param name="tipoDocumento" select="local-name()"/></xsl:call-template>
                <!-- il lifecycle viene creato al momento per la sola generazione -->
                <xsl:call-template name="crea.lifecycle"/>
                <!-- il workflow viene creato per il solo ddlpres -->
                <xsl:if test="local-name()='DDLPRES'"><xsl:call-template name="crea.workflow"><xsl:with-param name="iter" select="dl:Frontespizio/dl:Iter"/></xsl:call-template></xsl:if>
                <xsl:call-template name="crea.references.Main"/>
                <xsl:call-template name="crea.notes"><xsl:with-param name="note" select="//cm:Nota"/></xsl:call-template>
            </xsl:element>
            <xsl:choose>
                <xsl:when test="local-name()='DDLCOMM'">
                    <xsl:call-template name="crea.coverPage.DDLCOMM">
                        <xsl:with-param name="frontespizio" select="dl:Frontespizio"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:when test="local-name()='DDLMESS'">
                    <xsl:call-template name="crea.coverPage.DDLMESS">
                        <xsl:with-param name="frontespizio" select="dl:Frontespizio"/>
                    </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:call-template name="crea.coverPage.DDLPRES">
                        <xsl:with-param name="frontespizio" select="dl:Frontespizio"/>
                    </xsl:call-template>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:if test="local-name()='DDLMESS'">
                <xsl:call-template name="crea.preamble"><xsl:with-param name="messaggio" select="dl:Frontespizio/dl:Messaggio"/></xsl:call-template>
            </xsl:if>
            
            <xsl:call-template name="crea.body">
                <xsl:with-param name="articolato" select="a:Articolato[1]"/>
            </xsl:call-template>
            <xsl:call-template name="crea.attachments">
                <xsl:with-param name="allegati" select="$listaAllegati"/>
            </xsl:call-template>
        </xsl:element>

    </xsl:template>

 <!-- 
        ================================================ IDENTIFICATION FRBR ================================================  
 -->

    <!-- creazione elemento identification -->
    <xsl:template name="crea.identification.Main">
        <xsl:param name="tipoDocumento" as="xs:string"/>
        <xsl:param name="listaImmagini"/>
        <!-- richiesta l'identification per il main (globale) 
        <xsl:message><xsl:text>tipo (Main):</xsl:text><xsl:value-of select="$tipoDocumento"></xsl:value-of></xsl:message> -->
        <an:identification source="#redattore">
            <an:FRBRWork>
                <an:FRBRthis value="{concat($URIWork,'/main')}"/>
                <an:FRBRuri value="{$URIWork}"/>
                <an:FRBRdate date="{$docDate}" name="presentazione"/>
                <an:FRBRauthor href="#senato"/>
                <xsl:call-template name="crea.componentInfo"><xsl:with-param name="isMain" select="true()"/><xsl:with-param name="uri" select="concat($URIWork, $placeholder)"/><xsl:with-param name="sezione" select="'w'"/><xsl:with-param name="listaImmagini" select="$listaImmagini"/></xsl:call-template>
                <an:FRBRcountry value="ita"/>
                <an:FRBRsubtype value="{$tipoDocumento}"/>
                <an:FRBRnumber value="{$docNumber}"/>
                <an:FRBRname value="{$descrizioneTipoDoc}"/>
            </an:FRBRWork>
            <an:FRBRExpression>
                <an:FRBRthis value="{concat($URIExpression,'/main')}"/>
                <an:FRBRuri value="{$URIExpression}"/>
                <an:FRBRdate date="{$docDate}" name="presentazione"/>
                <an:FRBRauthor href="#senato"/>
                <xsl:call-template name="crea.componentInfo"><xsl:with-param name="isMain" select="true()"/><xsl:with-param name="uri" select="concat($URIWork, '/ita@', $placeholder)"/><xsl:with-param name="sezione" select="'e'"/><xsl:with-param name="listaImmagini" select="$listaImmagini"/></xsl:call-template>
                <an:FRBRlanguage language="it"/>
            </an:FRBRExpression>
            <!-- la manifestazione è proprio il file akoma che si vuole creare -->
            <an:FRBRManifestation>
                <an:FRBRthis value="{concat($URIExpression,'/main.xml')}"/>
                <an:FRBRuri value="{$URIManifestation}"/>
                <an:FRBRdate date="{$docDate}" name="presentazione"/>
                <an:FRBRauthor href="#redattore"/>
                <xsl:call-template name="crea.componentInfo"><xsl:with-param name="isMain" select="true()"/><xsl:with-param name="uri" select="concat($URIWork, '/ita@', $placeholder, '.xml')"/><xsl:with-param name="sezione" select="'m'"/><xsl:with-param name="listaImmagini" select="$listaImmagini"/></xsl:call-template>
            </an:FRBRManifestation>
        </an:identification>
    </xsl:template>

    <xsl:template name="crea.identification.Annex">
        <xsl:param name="tipoDocumento" as="xs:string"/>
        <xsl:param name="nomeR"/>
        <xsl:param name="nomeU"/>
        <xsl:param name="listaImmagini"></xsl:param>
        <!-- richiesta l'identification per un annesso 
        <xsl:message><xsl:text>tipo (Annex):</xsl:text><xsl:value-of select="$tipoDocumento"></xsl:value-of></xsl:message> -->
        <an:identification source="#redattore">
            <an:FRBRWork>
                <an:FRBRthis value=""/>
                <an:FRBRuri value="{concat($URIWork,'/main/',$nomeU)}"/>
                <an:FRBRdate date="{$docDate}" name="presentazione"/>
                <an:FRBRauthor href="#senato"/>
                <xsl:call-template name="crea.componentInfo"><xsl:with-param name="uri" select="concat($URIWork, '/ita@', $placeholder, '.xml')"/><xsl:with-param name="sezione" select="'w'"/><xsl:with-param name="listaImmagini" select="$listaImmagini"/></xsl:call-template>
                <an:FRBRcountry value="ita"/>
                <an:FRBRsubtype value="{$tipoDocumento}"/>
                <an:FRBRnumber value="{$docNumber}"/>
                <an:FRBRname value="{$nomeU}"/>
            </an:FRBRWork>
            <an:FRBRExpression>
                <an:FRBRthis value=""/>
                <an:FRBRuri value="{concat($URIExpression,'/main/',$nomeU)}"/>
                <an:FRBRdate date="{$docDate}" name="presentazione"/>
                <an:FRBRauthor href="#senato"/>
                <xsl:call-template name="crea.componentInfo"><xsl:with-param name="uri" select="concat($URIWork, '/ita@', $placeholder, '.xml')"/><xsl:with-param name="sezione" select="'e'"/><xsl:with-param name="listaImmagini" select="$listaImmagini"/></xsl:call-template>
                <an:FRBRlanguage language="it"/>
            </an:FRBRExpression>
            <!-- la manifestazione è proprio il file akoma che si vuole creare -->
            <an:FRBRManifestation>
                <an:FRBRthis value=""/>
                <an:FRBRuri value="{concat($URIExpression,'/main/', $nomeU, '.xml')}"/>
                <an:FRBRdate date="{$docDate}" name="presentazione"/>
                <an:FRBRauthor href="#redattore"/>
                <xsl:call-template name="crea.componentInfo"><xsl:with-param name="uri" select="concat($URIWork, '/ita@', $placeholder, '.xml')"/><xsl:with-param name="sezione" select="'m'"/><xsl:with-param name="listaImmagini" select="$listaImmagini"/></xsl:call-template>
            </an:FRBRManifestation>
        </an:identification>
    </xsl:template>

    <!-- crea componentinfo -->
    <xsl:template name="crea.componentInfo">
        <xsl:param name="uri"/>
        <xsl:param name="sezione"/>
        <xsl:param name="listaImmagini"/>
        <xsl:param name="isMain" as="xs:boolean" select="false()"/>
        
        <xsl:if test="$isMain or $listaImmagini">
            <an:componentInfo>
                <xsl:if test="$isMain">
                    <xsl:if test="/bgt:BGTDOC/*[1]/a:Articolato[1]">
                        <an:componentData id="{concat($sezione,'compmain')}" href="{replace($uri,$placeholder, '/main')}" showAs="{$descrizioneTipoDoc}" name="{$descrizioneTipoDoc}"/>
                    </xsl:if>
                    <xsl:for-each 
                        select="$listaAllegati" >
                        <xsl:variable name="numComponent" select="count(./preceding-sibling::*)"/>
                        <xsl:variable name="nomeR"><xsl:call-template name="decode.nomeAnnesso2readable"><xsl:with-param name="annesso" select="."/></xsl:call-template></xsl:variable>
                        <xsl:variable name="nomeU"><xsl:call-template name="decode.nomeAnnesso2URI"><xsl:with-param name="annesso" select="."/></xsl:call-template></xsl:variable>
                        <an:componentData id="{concat($sezione,'comp',$numComponent)}" href="{replace($uri,$placeholder,concat('/main/', $nomeU))}" showAs="{$nomeR}" name="{$nomeR}"/>
                    </xsl:for-each>
                </xsl:if>
                <xsl:if test="$listaImmagini">
                    <xsl:for-each select="$listaImmagini" >
                        <xsl:variable name="numComponent" select="position()"/>
<!--                        <xsl:variable name="numComponent" select="count(./preceding-sibling::*)"/> 
                        <xsl:message><xsl:text>sezione:</xsl:text><xsl:value-of select="$sezione"/><xsl:text>  numero:</xsl:text><xsl:value-of select="$numComponent"/></xsl:message> -->
                        <an:componentData id="{concat($sezione,'img',$numComponent,./@src)}" href="{concat($urlImmagini,./@src)}" showAs="{./@alt}" name="{./@title}"/>
                    </xsl:for-each>
                </xsl:if>
            </an:componentInfo>
        </xsl:if>
    </xsl:template>

    <!-- creazione elemento workflow -->
    <xsl:template name="crea.workflow">
        <xsl:param name="iter"/>
        <xsl:element name="an:workflow">
            <xsl:attribute name="source">#redattore</xsl:attribute>
            <!-- cicliamo su tutte le fase -->
            <xsl:for-each select="$iter/dl:Fase">
                <xsl:element name="an:step">
                    <xsl:attribute name="id">
                        <xsl:value-of select="concat('step', position())"/>
                    </xsl:attribute>
                    <xsl:variable name="tipoFase" select="local-name(./child::*[1])"/>
                    <xsl:variable name="dataFase">
                        <xsl:choose>
                            <xsl:when test=".//dl:Approvazione">
                                <xsl:value-of select=".//dl:Approvazione/@data"/>
                            </xsl:when>
                            <xsl:when test=".//dl:Trasmissione">
                                <xsl:value-of select=".//dl:Trasmissione/@data"/>
                            </xsl:when>
                            <xsl:otherwise/>
                        </xsl:choose>
                    </xsl:variable>
                    <xsl:attribute name="date">
                        <xsl:value-of select="$dataFase"/>
                    </xsl:attribute>
                    <xsl:attribute name="actor">
                        <xsl:text>#</xsl:text>
                        <xsl:value-of select="lower-case(@ramo)"/>
                    </xsl:attribute>
                    <xsl:attribute name="outcome">
                        <xsl:value-of select="$tipoFase"/>
                    </xsl:attribute>
                    <!-- riferimento allo stampato (nel caso di unificazione vale il primo) -->
                    <xsl:if test=".//dl:Stampato">
                        <xsl:attribute name="href">
                            <xsl:value-of
                                select="concat( 'it/Ddl/', $dataFase, '/', ./descendant::dl:Stampato[1]/@numero)"
                            />
                        </xsl:attribute>
                    </xsl:if>
                </xsl:element>
            </xsl:for-each>
        </xsl:element>
    </xsl:template>

    <!-- creazione delle note -->
    <xsl:template name="crea.notes">
        <xsl:param name="note"/>
        <xsl:if test="$note">
            <xsl:element name="an:notes">
                <xsl:attribute name="source"><xsl:text>#redattore</xsl:text></xsl:attribute>
                <xsl:for-each select="$note">
                    <xsl:element name="an:note">
                        <xsl:attribute name="id" select="generate-id(.)"/>
                        <xsl:choose>
                            <xsl:when test="count(./an:p)>0"><xsl:apply-templates select="./child::*"/></xsl:when>
                            <xsl:otherwise><xsl:element name="an:p"><xsl:apply-templates select="./child::*"/></xsl:element></xsl:otherwise>
                        </xsl:choose>
                    </xsl:element>
                </xsl:for-each>
            </xsl:element>
        </xsl:if>
    </xsl:template>

    <!-- creazione della sezione di allegati -->
    <xsl:template name="crea.attachments">
        <xsl:param name="allegati"/>
        <xsl:if test="$allegati">
            
            <xsl:element name="an:attachments">
                <xsl:for-each select="$allegati">
                    <xsl:variable name="numComponent" select="count(./preceding-sibling::*)"/>
                    <xsl:variable name="nomeR"><xsl:call-template name="decode.nomeAnnesso2readable"><xsl:with-param name="annesso" select="."/></xsl:call-template></xsl:variable>
                    <xsl:variable name="nomeU"><xsl:call-template name="decode.nomeAnnesso2URI"><xsl:with-param name="annesso" select="."/></xsl:call-template></xsl:variable>
                    <xsl:choose>
                        <xsl:when test="./local-name()='DecretoLegge'">
                            <xsl:call-template name="crea.decretoLegge">
                                <xsl:with-param name="decreto" select="."/>
                                <xsl:with-param name="nomeR" select="$nomeR"/>
                                <xsl:with-param name="nomeU" select="$nomeU"/>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:when test="./local-name()='Articolato'">
                            <xsl:call-template name="crea.articolato">
                                <xsl:with-param name="articolato" select="."/>
                                <xsl:with-param name="nomeR" select="$nomeR"/>
                                <xsl:with-param name="nomeU" select="$nomeU"/>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:call-template name="crea.doc">
                                <xsl:with-param name="doc" select="."/>
                                <xsl:with-param name="nomeR" select="$nomeR"/>
                                <xsl:with-param name="nomeU" select="$nomeU"/>
                            </xsl:call-template>
                        </xsl:otherwise>
                    </xsl:choose>
                    
                </xsl:for-each>
            </xsl:element>
        </xsl:if>
    </xsl:template>

    <!-- creazione dell'elemento lifecycle, per ora limitata alla sola generazione -->
    <xsl:template name="crea.lifecycle">
        <xsl:element name="an:lifecycle ">
            <xsl:attribute name="source">#redattore</xsl:attribute>
            <xsl:element name="an:eventRef">
                <xsl:attribute name="source">#ro1</xsl:attribute>
                <xsl:attribute name="id">event1</xsl:attribute>
                <xsl:attribute name="date" select="$docDate"/>
            </xsl:element>
        </xsl:element>
<!--        <an:lifecycle source="#redattore">
            <an:eventRef source="#ro1" id="event1" date="{$docDate}"/>
        </an:lifecycle> -->
    </xsl:template>

    <!-- creazione dell'elemento references -->
    <xsl:template name="crea.references.Main">
        <xsl:element name="an:references">
            <xsl:attribute name="source">#redattore</xsl:attribute>

            <!-- evento di generazione  -->
            <!-- TODO: verificare se il main ci vuole -->
            <xsl:element name="an:original">
                <xsl:attribute name="id">ro1</xsl:attribute>
                <xsl:attribute name="href" select="concat($URIExpression,'/main')"></xsl:attribute>
                <xsl:attribute name="showAs">generation</xsl:attribute>
            </xsl:element>
            
            <!-- indicazione degli attachments -->
            <xsl:for-each select="$listaAllegati">
                <xsl:variable name="numComponent" select="count(./preceding-sibling::*)"/>
                <xsl:variable name="nomeU"><xsl:call-template name="decode.nomeAnnesso2URI"><xsl:with-param name="annesso" select="."/></xsl:call-template></xsl:variable>
                <xsl:variable name="nomeR"><xsl:call-template name="decode.nomeAnnesso2readable"><xsl:with-param name="annesso" select="."/></xsl:call-template></xsl:variable>
                <xsl:element name="an:hasAttachment">
                    <xsl:attribute name="id" select="concat('annex',$numComponent)"/>
                    <xsl:attribute name="href" select="concat($URIExpression,'/main/',$nomeU)"/>
                    <xsl:attribute name="showAs" select="$nomeR"/>
                </xsl:element>
            </xsl:for-each>
            
            <!-- organizzazione Servizio informatica del Senato della Repubblica -->
            <xsl:element name="an:TLCOrganization">
                <xsl:attribute name="id">redattore</xsl:attribute>
                <xsl:attribute name="showAs"><xsl:text>Servizio Informatica del Senato della Repubblica</xsl:text></xsl:attribute>
                <xsl:attribute name="href"><xsl:text>/dati.senato.it/osr/Senato/Servizio Informatica</xsl:text></xsl:attribute>
            </xsl:element>

            <!-- organizzazione Senato della Repubblica -->
            <xsl:element name="an:TLCOrganization">
                <xsl:attribute name="id">senato</xsl:attribute>
                <xsl:attribute name="showAs">Senato della Repubblica</xsl:attribute>
                <xsl:attribute name="href">/dati.senato.it/osr/Senato</xsl:attribute>
            </xsl:element>

            <!-- organizzazione Camera dei Deputati -->
            <xsl:element name="an:TLCOrganization">
                <xsl:attribute name="id">camera</xsl:attribute>
                <xsl:attribute name="showAs">Camera dei Deputati</xsl:attribute>
                <xsl:attribute name="href">/dati.senato.it/osr/Camera</xsl:attribute>
            </xsl:element>

            <!-- inseriamo i ruoli (incarichi dei presentatori) -->
            <xsl:for-each
                select="//dl:Presentatore/@incarico[generate-id()=generate-id(key('listaIncarichi',.)[1])]">
                <xsl:variable name="ontologiaIncarico">
                    <xsl:choose>
                        <xsl:when test="upper-case(.)='DEPUTATO'">
                            <xsl:value-of select="concat($baseUriForOntologySenato,'Deputato')"/>
                        </xsl:when>
                        <xsl:when test="upper-case(.)='SENATORE'">
                            <xsl:value-of select="concat($baseUriForOntologySenato,'Senatore')"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of
                                select="concat($baseUriForOntologySenato,'IncaricoGoverno')"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:variable>
                <xsl:element name="an:TLCRole">
                    <xsl:attribute name="id">
                        <xsl:value-of select="generate-id()"/>
                    </xsl:attribute>
                    <xsl:attribute name="href">
                        <xsl:value-of select="$ontologiaIncarico"/>
                    </xsl:attribute>
                    <xsl:attribute name="showAs">
                        <xsl:value-of
                            select="concat(upper-case(substring(.,1,1)),
                        substring(.,2))"
                        />
                    </xsl:attribute>
                </xsl:element>
            </xsl:for-each>

            <!-- inseriamo i presentatori come persone -->
          
            <xsl:for-each select="//dl:Presentatore[generate-id()=generate-id(key('listaPersone',normalize-space(concat(./@nome,' ',./@cognome)))[1])]">
                <xsl:element name="an:TLCPerson">
                    <xsl:attribute name="id">
                        <xsl:value-of select="generate-id(.)"/>
                    </xsl:attribute>
                    <xsl:attribute name="href">
                        <xsl:value-of select="concat($baseUriForOntologySenato,'Persona')"/>
                    </xsl:attribute>
                    <xsl:attribute name="showAs">
<!--                        <xsl:value-of select="."/> -->
                        <xsl:value-of select="normalize-space(concat(@nome,' ',@cognome))"/>
                    </xsl:attribute>
                </xsl:element>
            </xsl:for-each>

        </xsl:element>
    </xsl:template>

    <xsl:template name="crea.references.Annex">
        <xsl:param name="annesso" />
        <xsl:param name="nomeR"/>
        <xsl:param name="nomeU"/>
        <xsl:variable name="numComponent" select="count($annesso/preceding-sibling::*)"/>
        
        <xsl:element name="an:references">
            <xsl:attribute name="source">#redattore</xsl:attribute>
            
            <!-- evento di generazione  -->
            <xsl:element name="an:original">
                <xsl:attribute name="id" select="concat('ro',$numComponent)"/>
                <xsl:attribute name="href" select="concat($URIExpression,'/main/', $nomeU)"></xsl:attribute>
                <xsl:attribute name="showAs" select="$nomeR"/>
            </xsl:element>
            
            <!-- attachment -->
            <xsl:element name="an:attachmentOf">
                <xsl:attribute name="id"  select="concat('mainAnx',$numComponent)"/>
                <xsl:attribute name="href" select="concat($URIExpression,'/main')"/>
                <xsl:attribute name="showAs" select="'Main'"/>
            </xsl:element>

        </xsl:element>
    </xsl:template>

    <!-- 
        creazione dell'elemento coverPage
        [TODO: al momento pensiamo ai semplici presentati che nascono ramo senato, 
        poi ci sarà da analizzare come gestire gli aspetti di workflow, ad esempio
        per gli atti che nascono come unificato, stralcio, ecc.]
    -->
    <xsl:template name="crea.coverPage.DDLPRES">
        <xsl:param name="frontespizio"/>

        <xsl:element name="an:coverPage">
            <!-- dichiarazione senato della repubblica -->
            <xsl:element name="an:p">SENATO DELLA REPUBBLICA</xsl:element>
            <!-- tipo documento -->
            <xsl:element name="an:p">
                <xsl:element name="an:docType">
                    <xsl:apply-templates select="$frontespizio/dl:TipoAtto"/>
                </xsl:element>
            </xsl:element>
            <!-- numero documento -->
            <xsl:element name="an:p">
                <xsl:element name="an:docNumber">
                    <xsl:apply-templates select="$frontespizio/dl:NumeroAtto"/>
                </xsl:element>
            </xsl:element>
            <!-- titolo documento -->
            <xsl:element name="an:p">
                <xsl:element name="an:docTitle">
                    <xsl:apply-templates select="$frontespizio/dl:Titolo"/>
                </xsl:element>
            </xsl:element>

            <!-- riportiamo qui l'iter -->
            <xsl:apply-templates select="$frontespizio/dl:Iter" mode="frontespizio"/>

        </xsl:element>
    </xsl:template>

    <xsl:template name="crea.coverPage.DDLMESS">
        <xsl:param name="frontespizio"/>
        <xsl:element name="an:coverPage">
            <!-- dichiarazione senato della repubblica -->
            <xsl:element name="an:p"><xsl:apply-templates select="$frontespizio/dl:Organo"/></xsl:element>

            <!-- numero documento -->
            <xsl:element name="an:p">
                <xsl:element name="an:docNumber">
                    <xsl:apply-templates select="$frontespizio/dl:NumeroAtto/@numero"/>
                </xsl:element>
            </xsl:element>
            
            <!-- titolo documento -->
            <xsl:element name="an:p">
                <xsl:element name="an:docTitle">
                    <xsl:apply-templates select="$frontespizio/following-sibling::a:Articolato[1]/a:TitoloAtto/child::node()"/>
                </xsl:element>
            </xsl:element>
            
        </xsl:element>
    </xsl:template>


    <xsl:template name="crea.coverPage.DDLCOMM">
        <xsl:param name="frontespizio"/>

        <xsl:element name="an:coverPage">
            <!-- dichiarazione senato della repubblica -->
            <xsl:element name="an:p">SENATO DELLA REPUBBLICA</xsl:element>
            <!-- tipo documento -->
            <xsl:element name="an:p">
                <xsl:element name="an:docType">
                    <xsl:apply-templates select="$frontespizio/dl:TipoAtto"/>
                </xsl:element>
            </xsl:element>
            <!-- numero documento -->
            <xsl:element name="an:p">
                <xsl:element name="an:docNumber">
                    <xsl:apply-templates select="$frontespizio/dl:NumeroAtto"/>
                </xsl:element>
            </xsl:element>
            <!-- relatore -->
            <xsl:element name="an:p">
                <xsl:element name="an:docIntroducer">
                    <xsl:apply-templates select="$frontespizio/dl:Relatore"/>
                </xsl:element>
            </xsl:element>

            <xsl:for-each select="$frontespizio/dl:Sezione">
                <xsl:element name="an:container">
                    <xsl:attribute name="id" select="generate-id()"/>
                    <xsl:attribute name="name">Sezione</xsl:attribute>

                    <!-- preambolo della sezione -->
                    <xsl:element name="an:p">
                        <xsl:apply-templates select="dl:Preambolo"/>
                    </xsl:element>
                    <xsl:for-each select="./dl:Atto">
                        <xsl:element name="an:container">
                            <xsl:attribute name="id" select="generate-id()"/>
                            <xsl:attribute name="name">Atto</xsl:attribute>
                            <!-- numero dell'atto componente -->
                            <xsl:element name="an:p">
                                <xsl:element name="an:docNumber">
                                    <xsl:apply-templates select="dl:Numero/@numero"/>
                                </xsl:element>
                            </xsl:element>
                            <!-- titolo dell'atto componente -->
                            <xsl:element name="an:p">
                                <xsl:element name="an:docTitle">
                                    <xsl:apply-templates select="dl:Titolo"/>
                                </xsl:element>
                            </xsl:element>
                            
                            <!-- riportiamo qui l'iter per ogni atto della sezione sezione-->
                            <xsl:apply-templates select="dl:Iter" mode="frontespizio"/>
                        </xsl:element>
                    </xsl:for-each>
                </xsl:element>
            </xsl:for-each>

            <!-- titolo documento -->
            <xsl:element name="an:p">
                <xsl:element name="an:docTitle">
                    <xsl:apply-templates select="$frontespizio/dl:Titolo"/>
                </xsl:element>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- decreto legge allegato al principale -->
    <xsl:template name="crea.decretoLegge">
        <xsl:param name="decreto"/>
        <xsl:param name="nomeU"/>
        <xsl:param name="nomeR"/>
        <xsl:param name="n"/>
        <xsl:element name="an:act">
            <xsl:element name="an:meta">
                <xsl:call-template name="crea.identification.Annex">
                    <xsl:with-param name="tipoDocumento">allegato/DecretoLegge</xsl:with-param>
                    <xsl:with-param name="nomeR" select="$nomeR"/>
                    <xsl:with-param name="nomeU" select="$nomeU"/>
                    <xsl:with-param name="listaImmagini" select="$decreto//h:img"/>
                </xsl:call-template>
                <xsl:call-template name="crea.references.Annex">
                    <xsl:with-param name="annesso" select="$decreto"/>
                    <xsl:with-param name="nomeR" select="$nomeR"/>
                    <xsl:with-param name="nomeU" select="$nomeU"/>
                </xsl:call-template>
            </xsl:element>
            <xsl:element name="an:coverPage">
                <xsl:element name="an:p"><xsl:apply-templates select="$decreto/dl:EstremiPubblicazione"></xsl:apply-templates></xsl:element>
                <xsl:element name="an:p"><xsl:apply-templates select="$decreto/dl:Organo"></xsl:apply-templates></xsl:element>
                <xsl:element name="an:p"><xsl:apply-templates select="$decreto/dl:Titolo"></xsl:apply-templates></xsl:element>
            </xsl:element>
            <xsl:element name="an:preamble">
                <xsl:apply-templates select="$decreto/dl:Messaggio[1]"/>
            </xsl:element>
            <xsl:call-template name="crea.body"><xsl:with-param name="articolato" select="$decreto/a:Articolato[1]"></xsl:with-param></xsl:call-template>
            <xsl:element name="an:conclusions">
                <xsl:apply-templates select="$decreto/dl:Messaggio[count(preceding-sibling::dl:Messaggio)>0] | $decreto/dl:Chiusura  "></xsl:apply-templates>
            </xsl:element>
        </xsl:element>
    </xsl:template>
    
    <!-- un articolato allegato al principale -->
    <xsl:template name="crea.articolato">
        <xsl:param name="articolato"/>
        <xsl:param name="nomeU"/>
        <xsl:param name="nomeR"/>
            <xsl:element name="an:bill">
                <xsl:element name="an:meta">
                    <xsl:call-template name="crea.identification.Annex">
                        <xsl:with-param name="tipoDocumento">allegato/Articolato</xsl:with-param>
                        <xsl:with-param name="nomeR" select="$nomeR"/>
                        <xsl:with-param name="nomeU" select="$nomeU"/>
                        <xsl:with-param name="listaImmagini" select="$articolato//h:img"/>
                    </xsl:call-template>
                    <xsl:call-template name="crea.references.Annex">
                        <xsl:with-param name="annesso" select="$articolato"/>
                        <xsl:with-param name="nomeR" select="$nomeR"/>
                        <xsl:with-param name="nomeU" select="$nomeU"/>
                    </xsl:call-template>
                </xsl:element>
                <xsl:element name="an:coverPage">
                    <xsl:element name="an:p">
                        <xsl:element name="an:docTitle">
                            <xsl:apply-templates select="$articolato/a:TitoloAtto/child::node()"/>
                            <xsl:element name="an:eol"/>
                            <xsl:apply-templates select="$articolato/a:SottoTitoloAtto/child::node()"/>
                        </xsl:element>
                    </xsl:element>
                </xsl:element>
                <xsl:call-template name="crea.body"><xsl:with-param name="articolato" select="$articolato"></xsl:with-param></xsl:call-template>
            </xsl:element>
    </xsl:template>
    
    
    <xsl:template name="crea.doc">
        <xsl:param name="doc"/>
        <xsl:param name="nomeR"/>
        <xsl:param name="nomeU"/>
        <xsl:element name="an:doc">
            <xsl:choose>
                <xsl:when test="$doc/@inIndice!=''">
                    <xsl:attribute name="name" select="$doc/@inIndice"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:attribute name="name" select="$doc/local-name()"/>
                </xsl:otherwise>
            </xsl:choose>
            <!-- provvisorio -->
            <xsl:element name="an:meta">
                <xsl:call-template name="crea.identification.Annex">
                    <xsl:with-param name="tipoDocumento" select="concat('allegato/',$doc/local-name())"/>
                    <xsl:with-param name="nomeR" select="$nomeR"/>
                    <xsl:with-param name="nomeU" select="$nomeU"/>
                    <xsl:with-param name="listaImmagini" select="$doc//h:img"/>
                </xsl:call-template>
                <xsl:call-template name="crea.references.Annex">
                    <xsl:with-param name="annesso" select="$doc"/>
                    <xsl:with-param name="nomeR" select="$nomeR"/>
                    <xsl:with-param name="nomeU" select="$nomeU"/>
                </xsl:call-template>
            </xsl:element>
            <xsl:element name="an:mainBody">
                <xsl:apply-templates select="$doc"/>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- 
        mappatura degli elementi di frontespizio per l'iter 
    -->

    <!-- l'intero iter -->
    <xsl:template match="dl:Iter" mode="frontespizio">
        <xsl:apply-templates select="dl:Fase" mode="frontespizio"/>
    </xsl:template>

    <!-- la singola fase -->
    <xsl:template match="dl:Fase" mode="frontespizio">
        <xsl:apply-templates mode="frontespizio"/>
    </xsl:template>

    <!-- tipo di fase presentazione -->
    <xsl:template match="dl:Presentazione | dl:Unificazione | dl:Stralcio | dl:Generica" mode="frontespizio">
        <xsl:apply-templates mode="frontespizio"/>
    </xsl:template>

    <!-- iniziativa legislativa -->
    <xsl:template match="dl:Iniziativa" mode="frontespizio">
        <xsl:element name="an:p">
            <xsl:apply-templates mode="frontespizio"/>
        </xsl:element>
    </xsl:template>

    <!-- il presentatore (senatore, deputato, ministro...) -->
    <xsl:template match="dl:Presentatore" mode="frontespizio">
        <xsl:element name="an:docProponent">
            <xsl:attribute name="refersTo">
                <xsl:value-of select="concat('#',generate-id(key('listaPersone',normalize-space(concat(@nome, ' ',@cognome)))[1]))"/>
            </xsl:attribute>
            <xsl:attribute name="as">
                <xsl:value-of select="concat('#',generate-id(key('listaIncarichi',@incarico)[1]))"/>
            </xsl:attribute>
            <xsl:variable name="contenuto">
                <xsl:value-of select="."/>
            </xsl:variable>
            <xsl:choose>
                <xsl:when test="string-length(normalize-space($contenuto))>0">
                    <xsl:apply-templates/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:choose>
                        <xsl:when
                            test="upper-case(@incarico)='SENATORE' or upper-case(@incarico)='DEPUTATO'">
                            <xsl:value-of select="normalize-space(concat(@nome, ' ',@cognome))"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="@incarico"/>
                            <xsl:text> (</xsl:text>
                            <xsl:value-of select="normalize-space(concat(@nome, ' ',@cognome))"/>
                            <xsl:text>)</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:element>
    </xsl:template>

    <!-- il relatore -->
    <xsl:template match="dl:Relatore" mode="frontespizio">
        <xsl:element name="an:docIntroducer">
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <!-- dettagli della fase -->
    <xsl:template match="dl:Preambolo | dl:Trasmissione | dl:Stampato | dl:Approvazione" mode="frontespizio">
        <xsl:element name="an:p">
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <!-- elemento che crea il body del bill, che in akoma corrisponde all'articolato -->
    <xsl:template name="crea.body">
        <xsl:param name="articolato"/>
        <xsl:variable name="inIndice" as="xs:string"><xsl:value-of select="normalize-space($articolato/@inIndice)"/></xsl:variable>
        <xsl:element name="an:body">
            <xsl:attribute name="title">
                <xsl:choose>
                    <xsl:when test="normalize-space($articolato/a:TitoloAtto)!=''"><xsl:value-of select="normalize-space($articolato/a:TitoloAtto)"/></xsl:when>
                    <xsl:when test="$inIndice != ''"><xsl:value-of select="$inIndice"/></xsl:when>
                    <xsl:otherwise><xsl:text>Articolato</xsl:text></xsl:otherwise>
                </xsl:choose>
            </xsl:attribute>
            <xsl:apply-templates select="$articolato"/>
        </xsl:element>
        <xsl:if test="$articolato/following-sibling::dl:Altro[1][normalize-space(.)='IL PRESIDENTE']">
            <xsl:call-template name="crea.conclusions"><xsl:with-param name="conclusioni" select="$articolato/following-sibling::dl:Altro[1][normalize-space(.)='IL PRESIDENTE']"/></xsl:call-template>
        </xsl:if>
    </xsl:template>

    <xsl:template name="crea.conclusions">
        <xsl:param name="conclusioni"/>
        <xsl:element name="an:conclusions">
        <xsl:choose>
            <xsl:when test="$conclusioni/h:p">
                <xsl:apply-templates select="$conclusioni" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:element name="an:p"><xsl:apply-templates select="$conclusioni" /></xsl:element>
            </xsl:otherwise>
        </xsl:choose>
            
        </xsl:element>
    </xsl:template>

    <!-- scrittura della relazione di presentazione -->
    <xsl:template name="crea.preamble">
        <xsl:param name="messaggio"/>
        <xsl:element name="an:preamble">
            <xsl:apply-templates select="$messaggio/child::node()"/>
        </xsl:element>
    </xsl:template>


    <!-- 
    ================================================ ARTICOLATO ================================================  
    mappatura degli elementi dell'articolato, gli id vengono creati dall'xslt
    -->
    <xsl:template match="a:TitoloAtto"/>
    <xsl:template match="a:SottoTitoloAtto"/>

    <xsl:template match="a:Libro">
        <xsl:element name="an:book">
            <xsl:attribute name="id" select="generate-id(.)"/>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <xsl:template match="a:Parte">
        <xsl:element name="an:part">
            <xsl:attribute name="id" select="generate-id(.)"/>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <xsl:template match="a:Titolo">
        <xsl:element name="an:title">
            <xsl:attribute name="id" select="generate-id(.)"/>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <!-- questo non va bene, definizione provvisoria e da controllare -->
    <xsl:template match="a:Capo">
        <xsl:element name="an:chapter">
            <xsl:attribute name="id" select="generate-id(.)"/>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <xsl:template match="a:Sezione">
        <xsl:element name="an:section">
            <xsl:attribute name="id" select="generate-id(.)"/>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <xsl:template match="a:Articolo">
        <xsl:element name="an:article">
            <xsl:attribute name="id" select="generate-id(.)"/>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <xsl:template match="a:Comma">
        <xsl:element name="an:paragraph">
            <xsl:attribute name="id" select="generate-id(.)"/>
            <xsl:choose>
                <xsl:when test="a:Corpo">
                    <xsl:apply-templates/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates select="a:Num"/>
                    <xsl:element name="an:list">
                        <xsl:attribute name="id" select="generate-id(./a:Num)"/>
                        <xsl:apply-templates select="a:Alinea | a:Lettera"/>
                    </xsl:element>
                </xsl:otherwise>
            </xsl:choose>

        </xsl:element>
    </xsl:template>

    <xsl:template match="a:Rubrica">
        <xsl:element name="an:heading">
            <xsl:attribute name="id" select="generate-id(.)"/>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <xsl:template match="a:Num">
        <xsl:variable name="contenuto" select="."/>
        <xsl:choose>
            <xsl:when test="string-length(normalize-space($contenuto))=0">
                <xsl:element name="an:num">
                    <xsl:value-of select="@numero"/>
                </xsl:element>
            </xsl:when>
            <xsl:otherwise>
                <xsl:element name="an:num">
                    <xsl:apply-templates/>
                </xsl:element>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="a:Corpo">
        <xsl:element name="an:content">
            <xsl:attribute name="id" select="generate-id(.)"/>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <xsl:template match="a:Alinea">
        <xsl:element name="an:intro">
            <xsl:attribute name="id" select="generate-id(.)"/>
            <xsl:choose>
                <xsl:when test="count(h:p)=0">
                    <xsl:element name="an:p">
                        <xsl:apply-templates/>
                    </xsl:element>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:element>
    </xsl:template>

    <xsl:template match="a:Lettera">
        <xsl:element name="an:point">
            <xsl:attribute name="id" select="generate-id(.)"/>
            <xsl:choose>
                <xsl:when test="a:Corpo">
                    <xsl:apply-templates/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates select="a:Num"/>
                    <xsl:element name="an:list">
                        <xsl:attribute name="id" select="generate-id(./a:Num)"/>
                        <xsl:apply-templates select="a:Alinea | a:Numero"/>
                    </xsl:element>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:element>
    </xsl:template>

    <xsl:template match="a:Numero">
        <xsl:element name="an:point">
            <xsl:attribute name="id" select="generate-id(.)"/>
            <xsl:choose>
                <xsl:when test="a:Corpo">
                    <xsl:apply-templates/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates select="a:Num"/>
                    <xsl:element name="an:list">
                        <xsl:attribute name="id" select="generate-id(./a:Num)"/>
                        <xsl:apply-templates select="a:Alinea | a:Numero"/>
                    </xsl:element>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:element>
    </xsl:template>

    <xsl:template match="a:table">
        <!-- tabella per il testo a fronte -->
        <xsl:element name="an:table">
                <xsl:attribute name="id" select="generate-id()"/>
                <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>
    
    <xsl:template match="a:tr">
        <!-- riga per il testo a fronte -->
        <xsl:element name="an:tr">
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>
    
    <xsl:template match="a:PresentazioneTAF">
        <xsl:element name="an:hcontainer">
            <xsl:attribute name="name">Testo a fronte</xsl:attribute>
            <xsl:attribute name="id" select="generate-id()"/>
            <xsl:element name="an:num"></xsl:element>
            <xsl:element name="an:content">
                <xsl:attribute name="id" select="concat(generate-id(),'-c')"/>
                <xsl:apply-templates/>
            </xsl:element>
        </xsl:element>
    </xsl:template>

<!--
    ================================================ DECODIFICHE ================================================  
-->

    <!-- template che traduce la codifica del localname dell'allegato/annesso in path uri -->
    <xsl:template name="decode.nomeAnnesso2URI">
        <xsl:param name="annesso"/>
        <!--       <xsl:variable name="nomeU"><xsl:call-template name="decode.nomeAnnesso2readable"><xsl:with-param name="annesso" select="$annesso"/></xsl:call-template></xsl:variable>
        <xsl:value-of select="replace(normalize-space($nomeU),' ','')"/>  -->
        <xsl:variable name="nome" as="xs:string" select="local-name($annesso)"/>
        <xsl:choose>
            <xsl:when test="$nome='RelPres'">
                <xsl:text>relazione</xsl:text>
            </xsl:when>
            <xsl:when test="$nome='RelTec'">
                <xsl:text>relazioneTecnica</xsl:text>
            </xsl:when>
            <xsl:when test="$nome='RelTecTabelle'">
                <xsl:text>tabelleRelazioneTecnica</xsl:text>
            </xsl:when>
            <xsl:when test="$nome='RelTecAllegati'">
                <xsl:text>allegatoRelazioneTecnica</xsl:text>
            </xsl:when>
            <xsl:when test="$nome='AnalisiTecnicoNormativa'">
                <xsl:text>analisiTecnico-normativa</xsl:text>
            </xsl:when>
            <xsl:when test="$nome='Articolato'">
                <xsl:text>articolato</xsl:text>
            </xsl:when>
            <xsl:when test="$nome='Allegato' or $nome='Altro' ">
                <xsl:text>allegato</xsl:text>
            </xsl:when>
            <xsl:when test="$nome='ParereCommissione'">
                <xsl:text>parereCommissione</xsl:text>
            </xsl:when>
            <xsl:when test="$nome='Emendamenti'">
                <xsl:text>emendamenti</xsl:text>
            </xsl:when>
            <xsl:otherwise><xsl:text>annesso</xsl:text></xsl:otherwise>
        </xsl:choose>       
    </xsl:template>
    
    <!-- template che traduce la codifica del localname dell'allegato/annesso in formato esteso leggibile -->
    <xsl:template name="decode.nomeAnnesso2readable">
        <xsl:param name="annesso"/>
        <xsl:variable name="nome" as="xs:string" select="local-name($annesso)"/>
        <xsl:variable name="inIndice" as="xs:string" ><xsl:value-of select="$annesso/@inIndice"/></xsl:variable>
        <xsl:variable name="commissione" as="xs:string"><xsl:value-of select="$annesso/@commissione"/></xsl:variable>
        <xsl:choose>
            <xsl:when test="$inIndice != '' "><xsl:value-of select="$inIndice"/></xsl:when>
            <xsl:when test="$nome='RelPres'">
                <xsl:text>Relazione</xsl:text>
            </xsl:when>
            <xsl:when test="$nome='RelTec'">
                <xsl:text>Relazione Tecnica</xsl:text>
            </xsl:when>
            <xsl:when test="$nome='RelTecTabelle'">
                <xsl:text>Tabelle Relazione Tecnica</xsl:text>
            </xsl:when>
            <xsl:when test="$nome='RelTecAllegati'">
                <xsl:text>Allegato Relazione Tecnica</xsl:text>
            </xsl:when>
            <xsl:when test="$nome='AnalisiTecnicoNormativa'">
                <xsl:text>Analisi Tecnico-normativa</xsl:text>
            </xsl:when>
            <xsl:when test="$nome='Articolato'">
                <xsl:choose>
                    <xsl:when test="normalize-space($annesso/a:TitoloAtto)!=''"><xsl:value-of select="normalize-space($annesso/a:TitoloAtto)"/></xsl:when>
                    <xsl:when test="$inIndice != ''"><xsl:value-of select="$inIndice"/></xsl:when>
                    <xsl:otherwise><xsl:text>Articolato</xsl:text></xsl:otherwise>
                </xsl:choose>
                
            </xsl:when>
            <xsl:when test="$nome='Allegato' or $nome='Altro' ">
                <xsl:text>Allegato</xsl:text>
            </xsl:when>
            <xsl:when test="$nome='ParereCommissione'">
                <xsl:choose>
                    <xsl:when test="$commissione != ''"><xsl:value-of select="concat('Parere Commissione ' , $commissione)"/></xsl:when>
                    <xsl:otherwise><xsl:text>Parere Commissione</xsl:text></xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="$nome='Emendamenti'">
                <xsl:text>Emendamenti</xsl:text>
            </xsl:when>
            <xsl:otherwise><xsl:text>Annesso</xsl:text></xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- 
        ================================================ HTML ================================================  
     -->
    
    <!--  lista emendamenti -->
    <xsl:template match="dl:Emendamenti">
        <xsl:element name="an:amendmentLists">
            <an:meta>
                <an:identification source="">
                    <an:FRBRWork>
                        <an:FRBRthis value=""/>
                        <an:FRBRuri value=""/>
                        <an:FRBRdate date="{$docDate}" name=""/>
                        <an:FRBRauthor href=""/>
                        <an:FRBRcountry value=""/>
                    </an:FRBRWork>
                    <an:FRBRExpression>
                        <an:FRBRthis value=""/>
                        <an:FRBRuri value=""/>
                        <an:FRBRdate date="{$docDate}" name=""/>
                        <an:FRBRauthor href=""/>
                        <an:FRBRlanguage language=""/>
                    </an:FRBRExpression>
                    <an:FRBRManifestation>
                        <an:FRBRthis value=""/>
                        <an:FRBRuri value=""/>
                        <an:FRBRdate date="{$docDate}" name=""/>
                        <an:FRBRauthor href=""/>
                    </an:FRBRManifestation>
                </an:identification>
            </an:meta>
            <xsl:element name="an:collectionBody">
                <xsl:apply-templates select="em:EMEND"/>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <xsl:template match="em:EMEND">
        <xsl:variable name="emendDate" select="./em:Proprieta/em:Protocollo/@data"/>
        <xsl:element name="an:amendment">
            <an:meta>
                <an:identification source="">
                    <an:FRBRWork>
                        <an:FRBRthis value=""/>
                        <an:FRBRuri value=""/>
                        <an:FRBRdate date="{$emendDate}" name=""/>
                        <an:FRBRauthor href=""/>
                        <an:FRBRcountry value=""/>
                    </an:FRBRWork>
                    <an:FRBRExpression>
                        <an:FRBRthis value=""/>
                        <an:FRBRuri value=""/>
                        <an:FRBRdate date="{$emendDate}" name=""/>
                        <an:FRBRauthor href=""/>
                        <an:FRBRlanguage language=""/>
                    </an:FRBRExpression>
                    <an:FRBRManifestation>
                        <an:FRBRthis value=""/>
                        <an:FRBRuri value=""/>
                        <an:FRBRdate date="{$emendDate}" name=""/>
                        <an:FRBRauthor href=""/>
                    </an:FRBRManifestation>
                </an:identification>
            </an:meta>
            <!-- TODO: i metadati dell'emendamento sono stati buttati in cover page, ma non va bene -->
            <xsl:element name="an:coverPage">
                <xsl:element name="an:p">
                    <xsl:text>Numero:</xsl:text>
                    <xsl:apply-templates select="em:Numero"/>
                </xsl:element>
                <xsl:element name="an:p">
                    <xsl:apply-templates select="em:NotaNumero"/>
                </xsl:element>
                <xsl:if test="em:ExNumero">
                    <xsl:element name="an:p">
                        <xsl:text>Numero:</xsl:text>
                        <xsl:apply-templates select="em:ExNumero"/>
                    </xsl:element>
                </xsl:if>
                <xsl:element name="an:p">
                    <xsl:text>Firmatari:</xsl:text>
                </xsl:element>
                <xsl:for-each select="em:Firmatario">
                    <xsl:element name="an:p">
                        <xsl:apply-templates select="."/>
                    </xsl:element>
                </xsl:for-each>
                <xsl:if test="em:Esito">
                    <xsl:element name="an:p">
                        <xsl:text>Esito:</xsl:text>
                        <xsl:apply-templates select="em:Esito"/>
                    </xsl:element>
                </xsl:if>
                <xsl:if test="em:NotaEsito">
                    <xsl:element name="an:p">
                        <xsl:text>Nota:</xsl:text>
                        <xsl:apply-templates select="em:NotaEsito"/>
                    </xsl:element>
                </xsl:if>
                <xsl:for-each select="em:EsitoParereCommissione">
                    <xsl:element name="an:p">
                        <xsl:text>Parere della Commissione:</xsl:text>
                    </xsl:element>
                    <xsl:element name="an:p">
                        <xsl:apply-templates select="em:EsitoParereCommissione"/>
                    </xsl:element>
                </xsl:for-each>
            </xsl:element>

            <xsl:element name="an:amendmentBody">
                <xsl:element name="an:amendmentContent">
                    <xsl:apply-templates select="em:Testo/child::node()"/>
                </xsl:element>
            </xsl:element>

        </xsl:element>
    </xsl:template>

    <!-- 
        elementi cm:Nota
    -->
    <xsl:template match="cm:Nota">
        <xsl:element name="an:noteRef">
            <xsl:attribute name="href" select="concat('#',generate-id())"/>
            <xsl:attribute name="marker" select="@rimando"></xsl:attribute>
        </xsl:element>
    </xsl:template>

    <!-- 
        ================================================ HTML ================================================  
        elementi del name space html
        [TODO: verificare le eccezioni, visto che è possibile che Akoma non mappi tutti gli elementi XHTML]
    -->
    <xsl:template match="h:*">
        <xsl:variable name="nome">
            <xsl:value-of select="concat('an:',local-name())"/>
        </xsl:variable>
        <xsl:element name="{$nome}">
            <xsl:call-template name="copiaAttributiHTML"><xsl:with-param name="tagName" select="local-name()"/></xsl:call-template>
            <xsl:if  test="local-name()='table' or local-name()='ul' or local-name()='div' or local-name()='ol'">
                <xsl:attribute name="id" select="generate-id()"/>
            </xsl:if>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <!-- elementi da sostituire in base al parent <dl:TipoAtto><h:p> -->
    <xsl:template match="dl:TipoAtto/h:p">
        <xsl:element name="an:span">
            <xsl:call-template name="copiaAttributiHTML"><xsl:with-param name="tagName" select="local-name()"/></xsl:call-template>
            <xsl:apply-templates/>
        </xsl:element>
        <xsl:element name="an:eol"/>
    </xsl:template>

    <!-- se esiste un anchor interno (a con attributo name) questo va escluso -->
    <xsl:template match="h:a[@name]"></xsl:template>
    
    <!-- elementi che hanno un diverso corrispettivo o struttura in akoma -->
    <xsl:template match="h:br">
        <xsl:element name="an:eol"/>
    </xsl:template>

    <xsl:template match="h:td | h:th">
        <!-- gli elementi akoma non supportano altezza e allineamento del testo e richiedono la presenza di un elemento p al minimo -->
        <xsl:variable name="nome">
            <xsl:value-of select="concat('an:',local-name())"/>
        </xsl:variable>
        <xsl:element name="{$nome}">
            <xsl:copy-of select="@colspan | @rowspan"/>
            <xsl:choose>
                <xsl:when test="./child::h:p | ./child::h:img">
                    <xsl:apply-templates/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:element name="an:p">
                        <xsl:apply-templates/>
                    </xsl:element>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:element>
    </xsl:template>

    <xsl:template match="h:img">
        <xsl:choose>
            <xsl:when test="parent::h:p">
                <xsl:element name="an:img">
                    <xsl:call-template name="copiaAttributiHTML"><xsl:with-param name="tagName" select="local-name()"/></xsl:call-template>
                    <xsl:attribute name="src"><xsl:value-of select="concat($urlImmagini,@src)"/></xsl:attribute>
                    <xsl:apply-templates/>
                </xsl:element>
            </xsl:when>
            <xsl:otherwise>
                <xsl:element name="an:p">
                    <xsl:element name="an:img">
                        <xsl:call-template name="copiaAttributiHTML"><xsl:with-param name="tagName" select="local-name()"/></xsl:call-template>
                        <xsl:attribute name="src"><xsl:value-of select="concat($urlImmagini,@src)"/></xsl:attribute>
                        <xsl:apply-templates/>
                    </xsl:element>
                </xsl:element>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- elementi html che non hanno corrispettivo in akoma -->
    <xsl:template match="h:colgroup | h:col"/>
    <xsl:template match="h:thead">
        <xsl:apply-templates/>
    </xsl:template>
    <xsl:template match="h:tbody">
        <xsl:apply-templates/>
    </xsl:template>
    <xsl:template match="h:h1 | h:h2 | h:h3 | h:h4 | h:h5 | h:h6 " >
        <xsl:element name="an:p">
            <xsl:attribute name="class" select="local-name()"/>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>


    <xsl:template name="copiaAttributiHTML">
        <xsl:param name="tagName"/>
        <xsl:choose>
            <xsl:when test="$tagName='table' or $tagName='tr'">
                <xsl:copy-of select="@*[local-name()!='align' and local-name()!='width' and local-name()!='heigth' and local-name()!='class' and local-name()!='style'  and local-name()!='valign' ]"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:copy-of select="@*[local-name()!='width' and local-name()!='heigth' and local-name()!='class' and local-name()!='style' ]"/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:variable name="styleFromClass">
            <xsl:choose>
                <xsl:when test="@class='qr'">text-align:right;</xsl:when>
                <xsl:when test="@class='qc'">text-align:center;</xsl:when>
                <xsl:when test="@class='smallcaps'">font-variant:small-caps;</xsl:when>
                <xsl:otherwise/>
            </xsl:choose>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="$styleFromClass!='' and @style">
                <xsl:attribute name="style" select="concat($styleFromClass, @style)"/>
            </xsl:when>
            <xsl:when test="$styleFromClass='' and @style">
                <xsl:attribute name="style" select="@style"/>
            </xsl:when>
            <xsl:when test="$styleFromClass!='' ">
                <xsl:attribute name="style" select="$styleFromClass"/>
            </xsl:when>
            <xsl:otherwise/>
        </xsl:choose>
    </xsl:template>

</xsl:stylesheet>
