<!--
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 -->

<!--
  Simple transform of Solr query response into Solr Update XML compliant XML.
  When used in the xslt response writer you will get UpdaateXML as output.
  But you can also store a query response XML to disk and feed this XML to
  the XSLTUpdateRequestHandler to index the content. Provided as example only.
  See http://wiki.apache.org/solr/XsltUpdateRequestHandler for more info
 -->
<xsl:stylesheet version='1.0' xmlns:xsl='http://www.w3.org/1999/XSL/Transform'>
  <xsl:output media-type="text/xml" method="xml" indent="yes"/>

  <xsl:template match='/'>
    <add>
        <xsl:apply-templates select="response/result/doc"/>
    </add>
  </xsl:template>

  <!-- Ignore score (makes no sense to index) -->
  <xsl:template match="doc/*[@name='score']" priority="100">
  </xsl:template>

  <xsl:template match="doc">
    <xsl:variable name="pos" select="position()"/>
    <doc>
        <xsl:apply-templates>
          <xsl:with-param name="pos"><xsl:value-of select="$pos"/></xsl:with-param>
        </xsl:apply-templates>
    </doc>
  </xsl:template>

  <!-- Flatten arrays to duplicate field lines -->
  <xsl:template match="doc/arr" priority="100">
      <xsl:variable name="fn" select="@name"/>

      <xsl:for-each select="*">
		<xsl:element name="field">
		    <xsl:attribute name="name"><xsl:value-of select="$fn"/></xsl:attribute>
	        <xsl:value-of select="."/>
		</xsl:element>
      </xsl:for-each>
  </xsl:template>


  <xsl:template match="doc/*">
      <xsl:variable name="fn" select="@name"/>

	<xsl:element name="field">
	    <xsl:attribute name="name"><xsl:value-of select="$fn"/></xsl:attribute>
        <xsl:value-of select="."/>
	</xsl:element>
  </xsl:template>

  <xsl:template match="*"/>
</xsl:stylesheet>
