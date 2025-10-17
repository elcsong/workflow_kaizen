# Global EU RoHS compliance regulation summary

RoHS (Restriction of Hazardous Substances) was initiated as and EU directive 2022/95/EC, to restrict 6 substances concentration in homogenous materials of defined electrical and electronic equipment (EEE). As time progressed, redefined product categories and additional restricted substances have been added to the legislation.

Several other countries/regions model “EU RoHS” to regulate their own country RoHS (such as: China RoHS, UAE RoHS, etc.).

The EU intention for promulgation RoHS, is to reduce the impact to the environment and to human health from the heavy metals, flame retardants, or phthalates in the EEEs when they become “waste”. The EU continues to monitor hazardous substances for future restrictions, while other countries typically follow the EU lead.


 

## EU Conformity Assessment Standard

RoHS regulatory requirements result in the evaluation of the whole product life cycle, from the product design, supply chain, product use, to recycling after end of life. In order to guide manufacturers to meet the conformity compliance, EU released harmonized standard “EN 50581” (repealed by IEC 63000 later) to guide manufacturers to assess whether the products are compliant. This standard provides procedures on how to perform the assessment, and how to collect and organize the assessment information. Additionally, the evidence for every part or component is required to be archived in the record for at least ten years.


 

## Relationship with REACH, Package, Battery, Mercury directives and regulation

Besides RoHS, the EU has established directive “2013/56/EU” to restrict the metal concentration (Mercury and Cadmium) in batteries and accumulators. Packaging is out of RoHS directive but restricted heavy metals (Mercury, Lead and Hexavalent Chromium) through directive “94/62/EC”. ‘Mercury Regulation’ (2017/852/EC) defined the phase-out time for some regulated products. EU REACH is a regulation with many kinds of substances restriction in article other than EEE. In many cases, these directives/regulations have overlap in the definition of the substances and their restriction thresholds, but they may also have additional substances or different threshold allowances when the substances are the same versus EU RoHS.

REACH has only “communication” requirements for substances above 1000 ppm listed in the SVHC-CLS (more than 200 substances and periodic update) w/o intended release, other directives in the table are “presence” limitation (under threshold) in products.
The concentration restriction in RoHS and Packaging directives are ‘homogenous’ versus the w/w (weight/weight) in Battery directive, and w/w of component/part in the article of REACH.
In other countries and some international standards, there are substance restriction requirements other than RoHS. For instance, Canada has the reporting requirements for DEHP/BPA when applying license for Health Canada, biocompatibility requirements, and phthalates labeling requirements per EN 15986. The file will not reflect these types of regulatory requirements.


 

## EU “Waste” legislation

RoHS is just a single part of the EU “Thematic Strategy on waste prevention and recycling” through which EU is systemically managing “waste”.

Directive EU 2018/851 (with amendment of 2008/98/EC) introduces the SCIP database
Marked in yellow defined the specific collection, recycling, and recovery targets.
All Waste Directives have an Environmental legal basis (Article 192 TFEU) with two exceptions: Batteries directive has double legal basis with an internal market basis covering specific articles that provide for full harmonization on metal content for batteries, labeling accepted on the market; and packaging Directive that has a full Internal Market legal basis (Article 114 TFEU)

 

## RoHS Requirements Elements

EU Commission initiated the RoHS directive 2022/95/EC with July 1, 2006 as compliance date in electrical and electronic equipment, which restricted 6 substances in homogeneous materials with concentration percentage.

EU Commission continuously published the recast of RoHS directive 2011/65/EU, namely “RoHS recast or RoHS II/2”, with expansion scope to cover all electrical and electric equipment, cable, spare parts by phased compliance times. Medical device as Category 8 from total 11 categories was required to meet RoHS 2 restriction after July 22, 2014, for 6 substances.

Directive (EU)2015/863 is an amendment of 2011/65/EU, which restricted 4 phthalates starting from July 22, 2019, though medical device compliance was not mandated until July 22, 2021.

EU Commission evaluates additional substances periodically to decide the next generation RoHS substances.


 

## Restricted Substances with concentration limitation

Currently EU RoHS restricts 10 substances: 4 metals, 2 Polybrominated Phenyl and 4 phthalates. All substances with restricted concentration threshold are listed:

Metals
n  Lead : 0.1%

n  Mercury: 0.1%

n  Cadmium: 0.01%

n  Hexavalent Chromium: 0.1%

Polybrominated Phenyl Compounds
n  Polybrominated biphenyls (PBB): 0.1%

n  Polybrominated diphenyl ethers (PBDE): 0.1%

Phthalates
n  Bis(2-ethylhexyl) phthalate (DEHP): 0.1%

n  Butyl benzyl phthalate (BBP): 0.1%

n  Dibutyl phthalate (DBP): 0.1%

n  Diisobutyl phthalate (DIBP): 0.1%

Other countries followed the EU restricted substances completely or partially.


 

## Substance Exemption

Substance exemptions are the permissions to use the restricted substance above the threshold in the scope/scenario for a specific duration when the substitution is not possible from the scientific and technical point of view. The decision on exemptions should also consider the impact of socioeconomic and the impact to environment, human safety etc. by substitution as well other relevant factors. Please see Appendix B for EU RoHS substance exemption renewal, review, and update.

EU is open on the policies and procedures of exemption renewal, and would publish and update all relevant information about exemptions such as submitted renewal requests, consultations, evaluation procedures etc. Here (https://ec.europa.eu/environment/waste/rohs_eee/adaptation_en.htm) for more information.

Other “Country-RoHS” usually define the substance exemptions based on EU RoHS, though they may not have individual evaluation procedures to generate or renew exemption. Additionally, they may adopt obsolete EU exemptions with different details.


 

## Product Scope

### EU RoHS Product Categories

The product scope for EU RoHS and all other Country-RoHS means the regulated and applicable products placing on the market. EU RoHS directive categorized EEE products into 11 groups and listed in Annex I of 2011/65/EU which almost covered all EEEs across consumer and industry sectors

EU RoHS Product Category
n  1: Large household appliances

n  2: Small household appliances

n  3: IT and telecommunications equipment

n  4: Consumer equipment

n  5: Lighting equipment

n  6: Electrical and electronic tools

n  7: Toys, leisure, and sports equipment

n  8: Medical devices

n  9: Monitoring and control instruments including industrial monitoring and control instruments

n  10: Automatic dispensers

n  11: Other EEE not covered by any of the categories above.

For other countries, UAE, Turkey, Vietnam, and Ukraine used same categorizing methods as EU to regulate the products, but Vietnam did not include Category 8 medical devices. China RoHS II marking requirements apply to all EEEs but did not categorize products. Other countries’ scope are mostly consumer or household products.


 

```Appendix A. Diagram

flowchart TD

    A[Start] --> O{Column O Mandatory}

    O -->|No| END0[End Mandatory No]

    O -->|Yes| TYP{Non medical device or Medical device}


 

    %% Non-medical branch

    TYP -->|Non medical| HCHK[Check Column H Product Scope]

    HCHK --> SCOPE_NMD{In scope by Column H}

    SCOPE_NMD -->|No| END1[End Out of scope]

    SCOPE_NMD -->|Yes| MARKET


 

    %% Medical branch

    TYP -->|Medical| LMN[Check Columns L M N]

    LMN --> SCOPE_MD{In scope by L M N}

    SCOPE_MD -->|No| END2[End Out of scope]

    SCOPE_MD -->|Yes| MARKET


 

    %% Market selection

    MARKET[Select targeted market by Column C Country] --> REQ[Market access requirements Columns P R S T U]


 

    %% P - Substance restriction

    REQ --> P{Column P Substance restriction required}

    P -->|Yes| TF[Prepare technical file as internal procedure]

    P -->|No| RQ

    TF --> RQ


 

    %% R - Marking

    RQ{Column R Marking required}

    RQ -->|Yes| MARK[Prepare marking]

    RQ -->|n a| SQ

    MARK --> SQ


 

    %% S and Q - Conformity assessment and scheme

    SQ{Column S Conformity assessment required}

    SQ -->|Yes| SCHEME[Select scheme by Column Q and perform assessment or pre approval]

    SQ -->|n a| TQ

    SCHEME --> TQ


 

    %% T - DoC accompanying

    TQ{Column T DoC accompanying product or digital}

    TQ -->|Yes| DOC[Prepare DoC and accompanying file]

    TQ -->|n a| UQ

    DOC --> UQ


 

    %% U - Validity

    UQ{Column U Validity info available}

    UQ -->|Yes| UV[Plan renewal and manage validity]

    UQ -->|n a| END3[End]

    UV --> END4[End]

```


 

### Acessories, A “STANDALONE” product as a part/component of a medical device.

EU RoHS applies to each part of finished EEEs including update part or service part, but only finished product needs to be declared and marked with CE. This is the same in other countries’ RoHS with individual parts/components able to opt to have individual declaration with marking. Accessories will not be part of the medical device but are treated as “standalone” products which may fall in RoHS regulated scope in some of countries.

Cables, spare parts for the repair, the reuse, the updating of functionalities or upgrading of capacity for a specific product category, must comply from the same date as their respective product category. Following the principle of ‘repair as produced’, spare parts for the specifiac products already on the market before the dates specially mentioned are exempted. Cables that are used for the transfer of electrical currents or electromagnetic fields are EEEs. Specialized cables such as SCART-cables, HDMI-cables, and network-cables, which are used for example in voice, data, and video transfer, are in categories 3 or 4 in EU RoHS, Non-finished cables such as cable reels without plugs can be classified as category 11. Essentially, other Country-RoHS also follow these same principles. Appendix A gives the details about whether a medical device, a part of a medical device or standalone products are in regulated scope or not.


 

## Product Exclusion

Section 4 of article 2 in 2011/65/EU lists the product Exclusion for EU RoHS, which are out of EU RoHS:

Equipment which is necessary for the protection of the essential interests of the security of Member States, including arms, munitions and war material intended for specifically military purposes;
Equipment designed to be sent into space;
Equipment which is specifically designed, and is to be installed, as part of another type of equipment that is excluded or does not fall within the scope of this Directive, which can fulfil its function only if it is part of that equipment, and which can replaced only by the same specifically designed equipment;
Large-scale stationary industrial tools;
Large-scale fixed installations;
Means of transport for persons or goods, excluding electric two-wheel vehicles which are not type-approved;
Non-road mobile machinery made available exclusively for professional use;
Active implantable medical devices;
Photovoltaic panels intended to be used in a system that is designed, assembled and installed by professionals for permanent use at a defined location to produce energy from solar light for public, commercial, industrial and residential applications;
Equipment specifically designed solely for the purposes of research and development only made available on a business-to-business basis.
Other Country-RoHS follows EU with the similar product exclusion. For those countries such Korea, Japan, Taiwan, Singapore etc. they have such few products defined as in-scope for RoHS or only focus on the consumer/household products, that these countries do not have to define the product exclusion.


 

### “Battery” and “Package” to RoHS

Packaging is out of RoHS scope for all countries/regions. Similarly, battery is out of RoHS scope except for China and Saudi Arabia. China RoHS does not exclude any battery products from RoHS. For Saudi Arabia RoHS, the batteries product with HTS prefix 8506- and 8548- are listed in the Annex (2-b) of Saudi Arabia Act Directors No. (179) even standalone shipped spare part of medical device it out of impact.


 

## Conformity Assessment

### Procedures for Assessing the Conformity of EEE (EU)

Substance restriction in EU RoHS requires manufacturers to use a systematic method to ensure that every part, every component in the EEEs is under the threshold, as well as ensuring that there is not any contaminating during manufacturing of a product. The harmonizing standard EN IEC 63000 (repealed EN 50581) provided the procedures for assessing the conformity of EEE subject to EU RoHS directive. The standard results in a technical documentation which is required to be archived for at least 10 years.

#### Technical File

The technical documentation shall include at least the following elements:

Product description
Information of every material, part, and/or component (Bill of Material) with corresponding conformity evidence
Used standard or technical specification for the conformity evidence
Review information or possible evaluation information
#### Process to assessment

IEC 63000 provides assessment processes of needed information determination, collection, and evaluation.


 

### EU Declaration of Conformity (EU)

The article 7 “Obligations of manufacturers” mandates the manufacturers to draw up the EU declaration of conformity according to the template in Annex 6 of the directive, with compliance demonstration, model structure, in required languages, the declaration context may be together with other applicable EU legislation.


 

### Conformity Assessment for Country-RoHS

Though EU RoHS provided a good methodology of how to assess the product compliance under the circumstance of global manufacturing supply, other countries may have their own situations and considerations. Most of countries followed EU’s methods and required manufacturers to have their own assessment but in some of countries, Pre-Market Actions (e.g., pre-approval) must be taken and some of countries do not have to demonstrate any Conformity Declaration while just requiring manufacturers to control or mange by themselves.


 

## Labeling and Marking Requirements

EU RoHS directive is one of “CE” scheme, and the finished EEEs have to affix the “CE” mark with products. For other country-RoHS, it may also be one of country “regulation” schemes which needs a scheme “mark” accompanying with product, or some of country-RoHS has individual RoHS mark.