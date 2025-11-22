<template>
  <b-jumbotron header="Privacy Policy" lead="Last updated: <strong>November 22, 2025</strong>">
    <p class="text-justify">
      <h4>1. Controller and Overview</h4>
      The
      <router-link :to="{name: 'home'}">slotlist.online</router-link> team ("we", "us" or "our") operates the website
      <router-link :to="{name: 'home'}">slotlist.online</router-link> (the "Service").
      <br>This privacy policy informs you about the collection, processing and use of your personal data when using our Service.
      <br>
      <br>
      <h4>2. Data Processing Principles</h4>
      Your privacy and information security is very important to us. We process your data only on the basis of legal provisions, in particular the General Data Protection Regulation (GDPR).
      <br>
      <br>
      <h4>3. Collection and Use of Personal Data</h4>
      <strong>3.1 When Using the Service</strong>
      <br>We collect and process the following personal data:
      <ul>
        <li>Your Steam ID 64</li>
        <li>Your Steam nickname (from the publicly available data of your Steam profile)</li>
        <li>Any other information you actively enter into our Service</li>
      </ul>
      <strong>Important:</strong> Our Service never receives your Steam username, password, the email address associated with your Steam account, or any other sensitive Steam account data.
      <br>
      <br>
      <strong>3.2 Legal Basis</strong>
      <br>The processing of your data is based on:
      <ul>
        <li>Art. 6 para. 1 lit. b GDPR (contract fulfillment)</li>
        <li>Art. 6 para. 1 lit. a GDPR (your consent)</li>
        <li>Art. 6 para. 1 lit. f GDPR (legitimate interests)</li>
      </ul>
      <strong>3.3 Purposes of Data Processing</strong>
      <br>We use your data for:
      <ul>
        <li>Providing and improving our Service</li>
        <li>Ensuring the security of our Service</li>
        <li>Communicating with you</li>
        <li>Fulfilling legal obligations</li>
      </ul>
      <br>
      <h4>4. Log Data</h4>
      We store information that your browser transmits when using our Service. This includes:
      <ul>
        <li>Your IP address</li>
        <li>Browser type and version</li>
        <li>Pages visited on our Service</li>
        <li>Date and time of access</li>
        <li>Duration of stay on pages</li>
        <li>Other statistics</li>
      </ul>
      <br>
      <h4>5. Cookies and Similar Technologies</h4>
      <strong>5.1 What are Cookies?</strong>
      <br>Cookies are small text files that are stored on your device.
      <br>
      <br>
      <strong>5.2 Cookies We Use</strong>
      <ul>
        <li>Essential Cookies: Required for the basic functionality of the Service</li>
        <li>Consent Cookie: Stores your cookie preferences</li>
      </ul>
      <strong>5.3 Third-Party Cookies</strong>
      <br>Our service provider Cloudflare may set cookies to better process requests.
      <br>
      <br>
      <strong>5.4 Cookie Management</strong>
      <br>You can reject or delete cookies in your browser settings. Please note that this may limit the functionality of our Service.
      <br>
      <br>
      <h4>6. Data Sharing with Third Parties</h4>
      <strong>6.1 General</strong>
      <br>We only share your data if:
      <ul>
        <li>You have consented (Art. 6 para. 1 lit. a GDPR)</li>
        <li>It is necessary for contract fulfillment</li>
        <li>There is a legal obligation</li>
      </ul>
      <strong>6.2 Current Service Providers</strong>
      <br>We use the following service providers:
      <table class="table table-sm">
        <thead>
          <tr>
            <th>Provider</th>
            <th>Service</th>
            <th>Data Processing</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><a href="https://cloudflare.com">Cloudflare</a></td>
            <td>DNS, CDN, DDoS protection</td>
            <td>USA (Adequacy Decision)</td>
          </tr>
          <tr>
            <td><a href="https://cloud.google.com">Google Cloud Platform</a></td>
            <td>Hosting (Frankfurt)</td>
            <td>EU</td>
          </tr>
        </tbody>
      </table>
      The privacy policies of these providers can be found on their respective websites.
      <br>
      <br>
      <h4>7. Your Rights</h4>
      You have the following rights regarding your personal data:
      <ul>
        <li>Right of access (Art. 15 GDPR)</li>
        <li>Right to rectification (Art. 16 GDPR)</li>
        <li>Right to erasure ("Right to be Forgotten", Art. 17 GDPR)</li>
        <li>Right to restriction of processing (Art. 18 GDPR)</li>
        <li>Right to data portability (Art. 20 GDPR)</li>
        <li>Right to object (Art. 21 GDPR)</li>
      </ul>
      To exercise these rights, please contact us through the channels mentioned in Section 11.
      <br>
      <br>
      <h4>8. External Links</h4>
      Our Service may contain links to external third-party websites. We have no control over their content and privacy practices and assume no responsibility for them.
      <br>
      <br>
      <h4>9. Children's Privacy</h4>
      Our Service is not directed at persons under 16 years of age. We do not knowingly collect personal data from children. If we have inadvertently collected data from children, we will delete it immediately.
      <br>
      <br>
      <h4>10. Changes to this Privacy Policy</h4>
      We reserve the right to update this privacy policy. We will inform you of significant changes by publishing the updated policy on this page.
      <br>
      <br>
      <h4>11. Contact</h4>
      If you have any questions about privacy, please contact us through the channels mentioned on our
      <router-link :to="{name: 'about'}">About</router-link> or
      <router-link :to="{name: 'imprint'}">Imprint</router-link> pages.
    </p>
  </b-jumbotron>
</template>

<script>
export default {
  name: 'PrivacyEN'
};
</script>
