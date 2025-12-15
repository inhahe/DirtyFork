<!DOCTYPE html>
<!-- saved from url=(0084)https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads -->
<html class="gl-light ui-neutral with-top-bar with-header  vivnjikn idc0_350" lang="en" style="--broadcast-message-height: 0px;"><head prefix="og: http://ogp.me/ns#"><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"><style>body {transition: opacity ease-in 0.2s; } 
body[unresolved] {opacity: 0; display: block; overflow: hidden; position: relative; } 
</style>

<meta content="IE=edge" http-equiv="X-UA-Compatible">
<meta content="width=device-width, initial-scale=1" name="viewport">
<title>src/sbbs3/zmodem.c · master · Main / Synchronet · GitLab</title>
<script>
//<![CDATA[
window.gon={};gon.api_version="v4";gon.default_avatar_url="https://gitlab.synchro.net/assets/no_avatar-849f9c04a3a0d0cea2424ae97b27447dc64a7dbfae83c036c45b403392f0e8ba.png";gon.max_file_size=10;gon.asset_host=null;gon.webpack_public_path="/assets/webpack/";gon.relative_url_root="";gon.user_color_mode="gl-light";gon.user_color_scheme="white";gon.markdown_surround_selection=null;gon.markdown_automatic_lists=null;gon.math_rendering_limits_enabled=true;gon.recaptcha_api_server_url="https://www.recaptcha.net/recaptcha/api.js";gon.recaptcha_sitekey=null;gon.gitlab_url="https://gitlab.synchro.net";gon.promo_url="https://about.gitlab.com";gon.forum_url="https://forum.gitlab.com";gon.docs_url="https://docs.gitlab.com";gon.revision="8a1c2c14173";gon.feature_category="groups_and_projects";gon.gitlab_logo="/assets/gitlab_logo-2957169c8ef64c58616a1ac3f4fc626e8a35ce4eb3ed31bb0d873712f2a041a0.png";gon.secure=true;gon.sprite_icons="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg";gon.sprite_file_icons="/assets/file_icons/file_icons-88a95467170997d6a4052c781684c8250847147987090747773c1ee27c513c5f.svg";gon.emoji_sprites_css_path="/assets/emoji_sprites-bd26211944b9d072037ec97cb138f1a52cd03ef185cd38b8d1fcc963245199a1.css";gon.emoji_backend_version=4;gon.gridstack_css_path="/assets/lazy_bundles/gridstack-4cd1da7c8adb8553e78a4f5545a8ab57a46258e091e6ac0382e6de79bca5ea3c.css";gon.test_env=false;gon.disable_animations=false;gon.suggested_label_colors={"#cc338b":"Magenta-pink","#dc143c":"Crimson","#c21e56":"Rose red","#cd5b45":"Dark coral","#ed9121":"Carrot orange","#eee600":"Titanium yellow","#009966":"Green-cyan","#8fbc8f":"Dark sea green","#6699cc":"Blue-gray","#e6e6fa":"Lavender","#9400d3":"Dark violet","#330066":"Deep violet","#36454f":"Charcoal grey","#808080":"Gray"};gon.first_day_of_week=0;gon.time_display_relative=true;gon.time_display_format=0;gon.ee=false;gon.jh=false;gon.dot_com=false;gon.uf_error_prefix="UF";gon.pat_prefix="glpat-";gon.keyboard_shortcuts_enabled=true;gon.diagramsnet_url="https://embed.diagrams.net";gon.features={"uiForOrganizations":false,"organizationSwitching":false,"findAndReplace":false,"removeMonitorMetrics":true,"workItemsViewPreference":true,"workItemViewForIssues":true,"searchButtonTopRight":false,"mergeRequestDashboard":false,"newProjectCreationForm":false,"workItemsClientSideBoards":false,"glqlWorkItems":false,"inlineBlame":false,"issueEmailParticipants":true,"editBranchRules":true,"pageSpecificStyles":false,"blobRepositoryVueHeaderApp":true,"blobOverflowMenu":true,"filterBlobPath":true,"directoryCodeDropdownUpdates":false,"workItems":true,"workItemsBeta":false,"workItemsAlpha":false};
//]]>
</script>


<script>
//<![CDATA[
var gl = window.gl || {};
gl.startup_calls = {"/main/sbbs/-/refs/master/logs_tree/?format=json\u0026offset=0\u0026ref_type=heads":{},"/main/sbbs/-/blob/master/README.md?format=json\u0026viewer=rich":{}};
gl.startup_graphql_calls = [{"query":"query pathLastCommit($projectPath: ID!, $path: String, $ref: String!, $refType: RefType) {\n  project(fullPath: $projectPath) {\n    __typename\n    id\n    repository {\n      __typename\n      lastCommit(path: $path, ref: $ref, refType: $refType) {\n        __typename\n        id\n        sha\n        title\n        titleHtml\n        descriptionHtml\n        message\n        webPath\n        authoredDate\n        authorName\n        authorGravatar\n        author {\n          __typename\n          id\n          name\n          avatarUrl\n          webPath\n        }\n        signature {\n          __typename\n          ... on GpgSignature {\n            gpgKeyPrimaryKeyid\n            verificationStatus\n          }\n          ... on X509Signature {\n            verificationStatus\n            x509Certificate {\n              id\n              subject\n              subjectKeyIdentifier\n              x509Issuer {\n                id\n                subject\n                subjectKeyIdentifier\n              }\n            }\n          }\n          ... on SshSignature {\n            verificationStatus\n            keyFingerprintSha256\n          }\n        }\n        pipelines(ref: $ref, first: 1) {\n          __typename\n          edges {\n            __typename\n            node {\n              __typename\n              id\n              detailedStatus {\n                __typename\n                id\n                detailsPath\n                icon\n                text\n              }\n            }\n          }\n        }\n      }\n    }\n  }\n}\n","variables":{"projectPath":"main/sbbs","ref":"master","path":""}}];

if (gl.startup_calls && window.fetch) {
  Object.keys(gl.startup_calls).forEach(apiCall => {
   gl.startup_calls[apiCall] = {
      fetchCall: fetch(apiCall, {
        // Emulate XHR for Rails AJAX request checks
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        },
        // fetch won’t send cookies in older browsers, unless you set the credentials init option.
        // We set to `same-origin` which is default value in modern browsers.
        // See https://github.com/whatwg/fetch/pull/585 for more information.
        credentials: 'same-origin'
      })
    };
  });
}
if (gl.startup_graphql_calls && window.fetch) {
  const headers = {"X-CSRF-Token":"GTLd__NfaclDQz_iPg0nkTJSKGCR6-3WTvAkXaKdOpVaJ-IpYioX6_Ktbwe98OVb8VpMa-QRRChha1P_TsAs6A","x-gitlab-feature-category":"groups_and_projects"};
  const url = `https://gitlab.synchro.net/api/graphql`

  const opts = {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...headers,
    }
  };

  gl.startup_graphql_calls = gl.startup_graphql_calls.map(call => ({
    ...call,
    fetchCall: fetch(url, {
      ...opts,
      credentials: 'same-origin',
      body: JSON.stringify(call)
    })
  }))
}


//]]>
</script>



<link rel="stylesheet" href="./synchronet sbbs zmodem_files/application-85890ef3e681d3f5327af0406c7aab607a6c961a82761ee93357494886f6896d.css">
<link rel="stylesheet" href="./synchronet sbbs zmodem_files/project-c979cd46017105b9bde03f4a30dd8e84ac39a0967c13eeda38a286ed67f1b137.css"><link rel="stylesheet" href="./synchronet sbbs zmodem_files/tree-3f0f40615de50f11e21c1a2cbc8e18f86c25dfdfa513ab6771b15a1784414691.css"><link rel="stylesheet" href="./synchronet sbbs zmodem_files/commit_description-1e2cba4dda3c7b30dd84924809020c569f1308dea51520fe1dd5d4ce31403195.css"><link rel="stylesheet" href="./synchronet sbbs zmodem_files/projects-16edafda8e98e20efce434e9cfbdade2d3a8fe5985cde756e285ae83598314d7.css"><link rel="stylesheet" href="./synchronet sbbs zmodem_files/work_items-719106b9e2288f0ecc75a8684a0312e38134efe78ac4cc5a9e7e37e93741fb3e.css"><link rel="stylesheet" href="./synchronet sbbs zmodem_files/notes_shared-dcc7282569d2548ab3f480f68ca656dfaffd9d58ccaf6c8aac8a297bd5249d1f.css">
<link rel="stylesheet" href="./synchronet sbbs zmodem_files/application_utilities-f77f86f78d4146d4c2c821bc481cee77b897df284886ad189d8dcb1234cb9651.css">
<link rel="stylesheet" href="./synchronet sbbs zmodem_files/tailwind-8a6161be68949b504e420e6e326210e08b447ec6230509ff23b0a9be20b24052.css">


<link rel="stylesheet" href="./synchronet sbbs zmodem_files/fonts-fae5d3f79948bd85f18b6513a025f863b19636e85b09a1492907eb4b1bb0557b.css">
<link rel="stylesheet" href="./synchronet sbbs zmodem_files/white-e4167b85702e96dd41cb029f9684388ac04731836d742ce6e8b65e2f8c2c96fd.css">

<script src="./synchronet sbbs zmodem_files/runtime.24239d66.bundle.js.download" defer="defer"></script>
<script src="./synchronet sbbs zmodem_files/main.acd40823.chunk.js.download" defer="defer"></script>
<script src="./synchronet sbbs zmodem_files/tracker.474aab07.chunk.js.download" defer="defer"></script>
<script>
//<![CDATA[
window.snowplowOptions = {"namespace":"gl","hostname":"gitlab.synchro.net:443","postPath":"/-/collect_events","forceSecureTracker":true,"appId":"gitlab_sm"}

gl = window.gl || {};
gl.snowplowStandardContext = {"schema":"iglu:com.gitlab/gitlab_standard/jsonschema/1-1-6","data":{"environment":"self-managed","source":"gitlab-rails","correlation_id":"01KBP0FBBH7VYVT1RDYZVQ6MWE","plan":"default","extra":{},"user_id":null,"global_user_id":null,"is_gitlab_team_member":null,"namespace_id":2,"ultimate_parent_namespace_id":2,"project_id":13,"feature_enabled_by_namespace_ids":null,"realm":null,"instance_id":null,"unique_instance_id":"93520057-2814-5493-8b30-bbf5630424f6","host_name":"gitlab.synchro.net","instance_version":"18.0.2","context_generated_at":"2025-12-05T01:01:57.703Z"}}
gl.snowplowPseudonymizedPageUrl = "https://gitlab.synchro.net/namespace2/project13";
gl.maskedDefaultReferrerUrl = "https://gitlab.synchro.net/";
gl.ga4MeasurementId = 'G-ENFH3X7M5Y';
gl.duoEvents = [];
gl.onlySendDuoEvents = false;


//]]>
</script>
<link rel="preload" href="./synchronet sbbs zmodem_files/application_utilities-f77f86f78d4146d4c2c821bc481cee77b897df284886ad189d8dcb1234cb9651.css" as="style" type="text/css">
<link rel="preload" href="./synchronet sbbs zmodem_files/application-85890ef3e681d3f5327af0406c7aab607a6c961a82761ee93357494886f6896d.css" as="style" type="text/css">
<link rel="preload" href="./synchronet sbbs zmodem_files/white-e4167b85702e96dd41cb029f9684388ac04731836d742ce6e8b65e2f8c2c96fd.css" as="style" type="text/css">
<link crossorigin="" href="https://events.gitlab.net/" rel="preconnect">
<link as="font" crossorigin="" href="https://gitlab.synchro.net/assets/gitlab-sans/GitLabSans-1e0a5107ea3bbd4be93e8ad2c503467e43166cd37e4293570b490e0812ede98b.woff2" rel="preload">
<link as="font" crossorigin="" href="https://gitlab.synchro.net/assets/gitlab-sans/GitLabSans-Italic-38eaf1a569a54ab28c58b92a4a8de3afb96b6ebc250cf372003a7b38151848cc.woff2" rel="preload">
<link as="font" crossorigin="" href="https://gitlab.synchro.net/assets/gitlab-mono/GitLabMono-08d2c5e8ff8fd3d2d6ec55bc7713380f8981c35f9d2df14e12b835464d6e8f23.woff2" rel="preload">
<link as="font" crossorigin="" href="https://gitlab.synchro.net/assets/gitlab-mono/GitLabMono-Italic-38e58d8df29485a20c550da1d0111e2c2169f6dcbcf894f2cd3afbdd97bcc588.woff2" rel="preload">
<link rel="preload" href="./synchronet sbbs zmodem_files/fonts-fae5d3f79948bd85f18b6513a025f863b19636e85b09a1492907eb4b1bb0557b.css" as="style" type="text/css">




<script src="./synchronet sbbs zmodem_files/commons-pages.admin.abuse_reports.show-pages.admin.topics.edit-pages.admin.topics.new-pages.groups.i-62354b5a.6612f85a.chunk.js.download" defer="defer"></script>
<script src="./synchronet sbbs zmodem_files/commons-pages.groups.harbor.repositories-pages.groups.new-pages.groups.packages-pages.groups.registr-aba9f596.88d51da4.chunk.js.download" defer="defer"></script>
<script src="./synchronet sbbs zmodem_files/commons-pages.search.show-super_sidebar.42cee40f.chunk.js.download" defer="defer"></script>
<script src="./synchronet sbbs zmodem_files/super_sidebar.7c5590c6.chunk.js.download" defer="defer"></script>
<script src="./synchronet sbbs zmodem_files/commons-pages.projects-pages.projects.activity-pages.projects.alert_management.details-pages.project-f24f3db4.4f50ca28.chunk.js.download" defer="defer"></script>
<script src="./synchronet sbbs zmodem_files/commons-pages.groups.packages-pages.groups.registry.repositories-pages.projects.blob.show-pages.proj-5dce5667.daffa06d.chunk.js.download" defer="defer"></script>
<script src="./synchronet sbbs zmodem_files/commons-pages.projects.blob.show-pages.projects.branches.new-pages.projects.commits.show-pages.proje-81161c0b.cb1f11af.chunk.js.download" defer="defer"></script>
<script src="./synchronet sbbs zmodem_files/31.6aa6bd19.chunk.js.download" defer="defer"></script>
<script src="./synchronet sbbs zmodem_files/commons-pages.projects.blob.show-pages.projects.show-pages.projects.snippets.edit-pages.projects.sni-42df7d4c.8474dd37.chunk.js.download" defer="defer"></script>
<script src="./synchronet sbbs zmodem_files/commons-pages.projects.artifacts.file-pages.projects.blob.show-pages.projects.show-pages.projects.sn-83d6e33b.d86739d3.chunk.js.download" defer="defer"></script>
<script src="./synchronet sbbs zmodem_files/commons-pages.projects.blob.show-pages.projects.show-pages.projects.snippets.show-pages.projects.tre-c684fcf6.ed9eaca8.chunk.js.download" defer="defer"></script>
<script src="./synchronet sbbs zmodem_files/commons-pages.projects.blob.edit-pages.projects.blob.new-pages.projects.blob.show-pages.projects.sho-ec79e51c.cfe6f84e.chunk.js.download" defer="defer"></script>
<script src="./synchronet sbbs zmodem_files/commons-pages.groups.show-pages.projects.blob.show-pages.projects.show-pages.projects.tree.show.be0d6395.chunk.js.download" defer="defer"></script>
<script src="./synchronet sbbs zmodem_files/commons-pages.projects.blob.show-pages.projects.show-pages.projects.tree.show-pages.search.show.17805021.chunk.js.download" defer="defer"></script>
<script src="./synchronet sbbs zmodem_files/commons-pages.projects.blob.show-pages.projects.show-pages.projects.tree.show.b0e66fdf.chunk.js.download" defer="defer"></script>
<script src="./synchronet sbbs zmodem_files/commons-pages.projects.home_panel-pages.projects.show.a5ab74f5.chunk.js.download" defer="defer"></script>
<script src="./synchronet sbbs zmodem_files/pages.projects.show.9b18640a.chunk.js.download" defer="defer"></script>

<meta content="object" property="og:type">
<meta content="GitLab" property="og:site_name">
<meta content="Main / Synchronet · GitLab" property="og:title">
<meta content="Synchronet source code, documentation and versioned run-time files." property="og:description">
<meta content="https://gitlab.synchro.net/uploads/-/system/project/avatar/13/2019-02-14.png" property="og:image">
<meta content="64" property="og:image:width">
<meta content="64" property="og:image:height">
<meta content="https://gitlab.synchro.net/main/sbbs" property="og:url">
<meta content="summary" property="twitter:card">
<meta content="Main / Synchronet · GitLab" property="twitter:title">
<meta content="Synchronet source code, documentation and versioned run-time files." property="twitter:description">
<meta content="https://gitlab.synchro.net/uploads/-/system/project/avatar/13/2019-02-14.png" property="twitter:image">

<meta name="csrf-param" content="authenticity_token">
<meta name="csrf-token" content="5JbTb1FY2QpqYt-WxxHCg3eYo8WIVCX7ksnCfyC-VR2ng-y5wC2nKNuMj3NE7ABJtJDHzv2ujAW9UrXdzONDYA">
<meta name="csp-nonce">
<meta name="action-cable-url" content="/-/cable">
<link href="https://gitlab.synchro.net/-/manifest.json" rel="manifest">
<link rel="icon" type="image/png" href="https://gitlab.synchro.net/uploads/-/system/appearance/favicon/1/sync_gitlab_favicon4.png" id="favicon" data-original-href="/uploads/-/system/appearance/favicon/1/sync_gitlab_favicon4.png">
<link rel="apple-touch-icon" type="image/x-icon" href="https://gitlab.synchro.net/assets/apple-touch-icon-b049d4bc0dd9626f31db825d61880737befc7835982586d015bded10b4435460.png">
<link href="https://gitlab.synchro.net/search/opensearch.xml" rel="search" title="Search GitLab" type="application/opensearchdescription+xml">
<link rel="alternate" type="application/atom+xml" title="Synchronet activity" href="https://gitlab.synchro.net/main/sbbs.atom">




<meta content="Synchronet source code, documentation and versioned run-time files." name="description">
<meta content="#ececef" name="theme-color">
<style>
svg[data-v-9534917c] {
  pointer-events: none;

  position: fixed;
  right: 0;
}
svg polygon[data-v-9534917c],
svg rect[data-v-9534917c] {
  pointer-events: auto;
}
</style><style>
.fake-input[data-v-26a01bbc] {
  position: absolute;
  top: 14px;
  left: 39px;
}
</style><style>
.input-box-wrapper[data-v-31424bc0] {
  position: relative;
}
.fake-input-wrapper[data-v-31424bc0] {
  position: absolute;
}
</style><script charset="utf-8" src="./synchronet sbbs zmodem_files/shortcutsBundle.94c47c24.chunk.js.download"></script><script charset="utf-8" src="./synchronet sbbs zmodem_files/hello.409c74c1.chunk.js.download"></script><style>
/* This is to override a margin caused by bootstrap */
.non-gfm-markdown-block {
p {
    margin-bottom: 0;
}
}
</style><style>
/* Temporary override until we have
   * widths available in GlDisclosureDropdown
   * https://gitlab.com/gitlab-org/gitlab-ui/-/issues/2501
   */
.code-dropdown .gl-new-dropdown-panel {
  width: 100%;
  max-width: 348px;
}
</style><style>
/* Temporary override until we have
   * widths available in GlDisclosureDropdown
   * https://gitlab.com/gitlab-org/gitlab-ui/-/issues/2501
   */
.code-dropdown .gl-new-dropdown-panel {
  width: 100%;
  max-width: 348px;
}
</style><script charset="utf-8" src="./synchronet sbbs zmodem_files/121.79545acb.chunk.js.download"></script><script charset="utf-8" src="./synchronet sbbs zmodem_files/vendors-treeList.e81c20d2.chunk.js.download"></script><script charset="utf-8" src="./synchronet sbbs zmodem_files/commons-pages.admin.abuse_reports.show-pages.admin.topics.edit-pages.admin.topics.new-pages.dashboar-b43963f0.d6fafff4.chunk.js.download"></script><script charset="utf-8" src="./synchronet sbbs zmodem_files/commons-pages.admin.abuse_reports.show-pages.admin.topics.edit-pages.admin.topics.new-pages.groups.i-1865123f.91e87b5f.chunk.js.download"></script><script charset="utf-8" src="./synchronet sbbs zmodem_files/treeList.eeb7c991.chunk.js.download"></script><script charset="utf-8" src="./synchronet sbbs zmodem_files/initInviteMembersTrigger.17b91217.chunk.js.download"></script><script charset="utf-8" src="./synchronet sbbs zmodem_files/IntegrationSectionAmazonQ.f9586ac0.chunk.js.download"></script><script charset="utf-8" src="./synchronet sbbs zmodem_files/948.faa74274.chunk.js.download"></script></head>

<body class="tab-width-8 gl-browser-edge gl-platform-windows body-fixed-scrollbar page-initialised" data-group="main" data-group-full-path="main" data-namespace-id="2" data-page="projects:show" data-page-type-id="sbbs" data-project="sbbs" data-project-full-path="main/sbbs" data-project-id="13" data-modal-open-count="0" style="">
<div id="js-tooltips-container"></div>

<script>
//<![CDATA[
gl = window.gl || {};
gl.client = {"isEdge":true,"isWindows":true};


//]]>
</script>


<header class="header-logged-out" data-testid="navbar">
<a class="gl-sr-only gl-accessibility" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#content-body">Skip to content</a>
<div class="container-fluid">
<nav aria-label="Explore GitLab" class="header-logged-out-nav gl-flex gl-gap-3 gl-justify-between">
<div class="gl-flex gl-items-center gl-gap-1">
<span class="gl-sr-only">GitLab</span>
<a title="Homepage" id="logo" class="header-logged-out-logo has-tooltip" aria-label="Homepage" data-track-label="main_navigation" data-track-action="click_gitlab_logo_link" data-track-property="navigation_top" href="https://gitlab.synchro.net/"><img class="brand-header-logo js-lazy-loaded" alt="" src="./synchronet sbbs zmodem_files/gitlab_powered_by_synchronet3.png" loading="lazy" data-testid="js-lazy-loaded-content">
</a></div>
<ul class="gl-list-none gl-p-0 gl-m-0 gl-flex gl-gap-3 gl-items-center gl-grow">
<li class="header-logged-out-nav-item">
<a class="" href="https://gitlab.synchro.net/explore">Explore</a>
</li>
</ul>
<ul class="gl-list-none gl-p-0 gl-m-0 gl-flex gl-gap-3 gl-items-center gl-justify-end">
<li class="header-logged-out-nav-item">
<a href="https://gitlab.synchro.net/users/sign_in?redirect_to_referer=yes">Sign in</a>
</li>
<li class="header-logged-out-nav-item">
<a class="gl-button btn btn-md btn-confirm !gl-inline-flex" href="https://gitlab.synchro.net/users/sign_up"><span class="gl-button-text">
Register

</span>

</a></li>
</ul>
</nav>
</div>
</header>

<div class="layout-page page-with-super-sidebar">
<div><div class="super-sidebar-overlay"></div> <!----> <nav id="super-sidebar" aria-labelledby="super-sidebar-heading" data-testid="super-sidebar" class="super-sidebar"><h2 id="super-sidebar-heading" class="gl-sr-only">
      Primary navigation
    </h2> <div class="user-bar gl-flex gl-gap-1 gl-p-3"><div class="gl-flex gl-items-center gl-gap-1"><!----> <button aria-controls="super-sidebar" aria-expanded="true" aria-label="Primary navigation sidebar" type="button" class="btn btn-default btn-md gl-button btn-default-tertiary btn-icon js-super-sidebar-toggle-collapse" data-testid="super-sidebar-collapse-button"><!----> <svg data-testid="sidebar-icon" role="img" aria-hidden="true" class="gl-button-icon gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#sidebar"></use></svg>  <!----></button> <!----> <!----> <!----></div> <!----> <!----> <div class="gl-grow"><button id="super-sidebar-search" data-testid="super-sidebar-search-button" type="button" class="btn user-bar-button gl-border-none btn-default btn-md btn-block gl-button"><!----> <!---->  <span class="gl-button-text"><svg data-testid="search-icon" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#search"></use></svg>
      Search or go to…
    </span></button> <!----></div></div> <div class="contextual-nav gl-flex gl-grow gl-flex-col gl-overflow-hidden"><div id="super-sidebar-context-header" class="super-sidebar-context-header gl-m-0 gl-px-4 gl-py-3 gl-font-bold gl-leading-reset">
        Project
      </div> <div class="gl-scroll-scrim gl-overflow-auto gl-grow" data-testid="nav-container"><div class="top-scrim-wrapper"><div class="top-scrim"></div></div> <div></div> <div class="gl-relative gl-p-2"><!----> <!----> <!----> <ul aria-labelledby="super-sidebar-context-header" data-testid="non-static-items-section" class="gl-mb-0 gl-list-none gl-p-0"><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs" aria-current="page" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus super-sidebar-nav-item-current gl-px-3 gl-rounded-base shortcuts-project" data-testid="nav-item-link" aria-label="Synchronet" data-track-action="click_menu_item" data-track-label="project_overview" data-track-property="nav_panel_project" data-qa-submenu-item="project-overview"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-10" style="width: 3px; border-radius: 3px; margin-right: 1px; transform: translateX(-1px);"></div> <div class="gl-flex gl-w-6 gl-shrink-0 gl-self-start"><img src="./synchronet sbbs zmodem_files/2019-02-14.png" alt="avatar" class="gl-avatar gl-avatar-s24"></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Synchronet
      <!----></div>  <!----></a> <!----></li><li><!----> <button id="menu-section-button-manage" data-testid="menu-section-button" data-qa-section-name="Manage" aria-controls="manage" aria-expanded="false" data-qa-menu-item="Manage" class="super-sidebar-nav-item gl-relative gl-mb-2 gl-flex gl-min-h-7 gl-w-full gl-appearance-none gl-items-center gl-gap-3 gl-rounded-base gl-border-0 gl-bg-transparent gl-px-3 gl-py-2 gl-text-left !gl-text-default !gl-no-underline focus:gl-focus"><span aria-hidden="true" class="gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-bg-transparent" style="width: 3px; border-radius: 3px; margin-right: 1px;"></span> <span class="gl-flex gl-w-6 gl-shrink-0"><svg data-testid="users-icon" role="img" aria-hidden="true" class="super-sidebar-nav-item-icon gl-m-auto gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#users"></use></svg></span> <span class="gl-truncate-end gl-grow gl-text-default">
      Manage
    </span> <span class="gl-text-right gl-text-subtle"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="gl-animated-icon gl-animated-icon-off gl-animated-icon-current"><path d="M6.75 4.75L10 8L6.75 11.25" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="gl-animated-chevron-right-down-arrow"></path></svg></span></button> <!----> <div class="gl-m-0 gl-list-none gl-p-0 gl-duration-medium gl-ease-ease collapse" id="manage" data-testid="menu-section" data-qa-section-name="Manage" style="display: none;"><ul aria-label="Manage" class="gl-m-0 gl-list-none gl-p-0"><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/activity" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base shortcuts-project-activity" data-testid="nav-item-link" aria-label="Activity" data-track-action="click_menu_item" data-track-label="activity" data-track-property="nav_panel_project" data-qa-submenu-item="Activity"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Activity
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/project_members" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base" data-testid="nav-item-link" aria-label="Members" data-track-action="click_menu_item" data-track-label="members" data-track-property="nav_panel_project" data-qa-submenu-item="Members"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Members
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/labels" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base" data-testid="nav-item-link" aria-label="Labels" data-track-action="click_menu_item" data-track-label="labels" data-track-property="nav_panel_project" data-qa-submenu-item="Labels"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Labels
      <!----></div>  <!----></a> <!----></li></ul></div></li><li><!----> <button id="menu-section-button-plan" data-testid="menu-section-button" data-qa-section-name="Plan" aria-controls="plan" aria-expanded="false" data-qa-menu-item="Plan" class="super-sidebar-nav-item gl-relative gl-mb-2 gl-flex gl-min-h-7 gl-w-full gl-appearance-none gl-items-center gl-gap-3 gl-rounded-base gl-border-0 gl-bg-transparent gl-px-3 gl-py-2 gl-text-left !gl-text-default !gl-no-underline focus:gl-focus"><span aria-hidden="true" class="gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-bg-transparent" style="width: 3px; border-radius: 3px; margin-right: 1px;"></span> <span class="gl-flex gl-w-6 gl-shrink-0"><svg data-testid="planning-icon" role="img" aria-hidden="true" class="super-sidebar-nav-item-icon gl-m-auto gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#planning"></use></svg></span> <span class="gl-truncate-end gl-grow gl-text-default">
      Plan
    </span> <span class="gl-text-right gl-text-subtle"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="gl-animated-icon gl-animated-icon-off gl-animated-icon-current"><path d="M6.75 4.75L10 8L6.75 11.25" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="gl-animated-chevron-right-down-arrow"></path></svg></span></button> <!----> <div class="gl-m-0 gl-list-none gl-p-0 gl-duration-medium gl-ease-ease collapse" id="plan" data-testid="menu-section" data-qa-section-name="Plan" style="display: none;"><ul aria-label="Plan" class="gl-m-0 gl-list-none gl-p-0"><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/issues" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base shortcuts-issues has-sub-items" data-testid="nav-item-link" aria-label="Issues" data-track-action="click_menu_item" data-track-label="project_issue_list" data-track-property="nav_panel_project" data-qa-submenu-item="Issues"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Issues
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/boards" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base shortcuts-issue-boards" data-testid="nav-item-link" aria-label="Issue boards" data-track-action="click_menu_item" data-track-label="boards" data-track-property="nav_panel_project" data-qa-submenu-item="Issue boards"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Issue boards
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/milestones" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base" data-testid="nav-item-link" aria-label="Milestones" data-track-action="click_menu_item" data-track-label="milestones" data-track-property="nav_panel_project" data-qa-submenu-item="Milestones"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Milestones
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/wikis/home" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base shortcuts-wiki" data-testid="nav-item-link" aria-label="Wiki" data-track-action="click_menu_item" data-track-label="project_wiki" data-track-property="nav_panel_project" data-qa-submenu-item="Wiki"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Wiki
      <!----></div>  <!----></a> <!----></li></ul></div></li><li><!----> <button id="menu-section-button-code" data-testid="menu-section-button" data-qa-section-name="Code" aria-controls="code" aria-expanded="false" data-qa-menu-item="Code" class="super-sidebar-nav-item gl-relative gl-mb-2 gl-flex gl-min-h-7 gl-w-full gl-appearance-none gl-items-center gl-gap-3 gl-rounded-base gl-border-0 gl-bg-transparent gl-px-3 gl-py-2 gl-text-left !gl-text-default !gl-no-underline focus:gl-focus"><span aria-hidden="true" class="gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-bg-transparent" style="width: 3px; border-radius: 3px; margin-right: 1px;"></span> <span class="gl-flex gl-w-6 gl-shrink-0"><svg data-testid="code-icon" role="img" aria-hidden="true" class="super-sidebar-nav-item-icon gl-m-auto gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#code"></use></svg></span> <span class="gl-truncate-end gl-grow gl-text-default">
      Code
    </span> <span class="gl-text-right gl-text-subtle"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="gl-animated-icon gl-animated-icon-off gl-animated-icon-current"><path d="M6.75 4.75L10 8L6.75 11.25" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="gl-animated-chevron-right-down-arrow"></path></svg></span></button> <!----> <div class="gl-m-0 gl-list-none gl-p-0 gl-duration-medium gl-ease-ease collapse" id="code" data-testid="menu-section" data-qa-section-name="Code" style="display: none;"><ul aria-label="Code" class="gl-m-0 gl-list-none gl-p-0"><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/merge_requests" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base shortcuts-merge_requests" data-testid="nav-item-link" aria-label="Merge requests" data-track-action="click_menu_item" data-track-label="project_merge_request_list" data-track-property="nav_panel_project" data-qa-submenu-item="Merge requests"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Merge requests
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/tree/master" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base shortcuts-tree" data-testid="nav-item-link" aria-label="Repository" data-track-action="click_menu_item" data-track-label="files" data-track-property="nav_panel_project" data-qa-submenu-item="Repository"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Repository
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/branches" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base" data-testid="nav-item-link" aria-label="Branches" data-track-action="click_menu_item" data-track-label="branches" data-track-property="nav_panel_project" data-qa-submenu-item="Branches"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Branches
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/commits/master?ref_type=heads" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base shortcuts-commits" data-testid="nav-item-link" aria-label="Commits" data-track-action="click_menu_item" data-track-label="commits" data-track-property="nav_panel_project" data-qa-submenu-item="Commits"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Commits
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/tags" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base" data-testid="nav-item-link" aria-label="Tags" data-track-action="click_menu_item" data-track-label="tags" data-track-property="nav_panel_project" data-qa-submenu-item="Tags"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Tags
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/network/master?ref_type=heads" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base shortcuts-network" data-testid="nav-item-link" aria-label="Repository graph" data-track-action="click_menu_item" data-track-label="graphs" data-track-property="nav_panel_project" data-qa-submenu-item="Repository graph"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Repository graph
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/compare?from=master&amp;to=master" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base" data-testid="nav-item-link" aria-label="Compare revisions" data-track-action="click_menu_item" data-track-label="compare" data-track-property="nav_panel_project" data-qa-submenu-item="Compare revisions"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Compare revisions
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/snippets" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base shortcuts-snippets" data-testid="nav-item-link" aria-label="Snippets" data-track-action="click_menu_item" data-track-label="project_snippets" data-track-property="nav_panel_project" data-qa-submenu-item="Snippets"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Snippets
      <!----></div>  <!----></a> <!----></li></ul></div></li><li><!----> <button id="menu-section-button-build" data-testid="menu-section-button" data-qa-section-name="Build" aria-controls="build" aria-expanded="false" data-qa-menu-item="Build" class="super-sidebar-nav-item gl-relative gl-mb-2 gl-flex gl-min-h-7 gl-w-full gl-appearance-none gl-items-center gl-gap-3 gl-rounded-base gl-border-0 gl-bg-transparent gl-px-3 gl-py-2 gl-text-left !gl-text-default !gl-no-underline focus:gl-focus"><span aria-hidden="true" class="gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-bg-transparent" style="width: 3px; border-radius: 3px; margin-right: 1px;"></span> <span class="gl-flex gl-w-6 gl-shrink-0"><svg data-testid="rocket-icon" role="img" aria-hidden="true" class="super-sidebar-nav-item-icon gl-m-auto gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#rocket"></use></svg></span> <span class="gl-truncate-end gl-grow gl-text-default">
      Build
    </span> <span class="gl-text-right gl-text-subtle"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="gl-animated-icon gl-animated-icon-off gl-animated-icon-current"><path d="M6.75 4.75L10 8L6.75 11.25" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="gl-animated-chevron-right-down-arrow"></path></svg></span></button> <!----> <div class="gl-m-0 gl-list-none gl-p-0 gl-duration-medium gl-ease-ease collapse" id="build" data-testid="menu-section" data-qa-section-name="Build" style="display: none;"><ul aria-label="Build" class="gl-m-0 gl-list-none gl-p-0"><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/pipelines" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base shortcuts-pipelines" data-testid="nav-item-link" aria-label="Pipelines" data-track-action="click_menu_item" data-track-label="pipelines" data-track-property="nav_panel_project" data-qa-submenu-item="Pipelines"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Pipelines
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/jobs" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base shortcuts-builds" data-testid="nav-item-link" aria-label="Jobs" data-track-action="click_menu_item" data-track-label="jobs" data-track-property="nav_panel_project" data-qa-submenu-item="Jobs"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Jobs
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/pipeline_schedules" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base shortcuts-builds" data-testid="nav-item-link" aria-label="Pipeline schedules" data-track-action="click_menu_item" data-track-label="pipeline_schedules" data-track-property="nav_panel_project" data-qa-submenu-item="Pipeline schedules"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Pipeline schedules
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/artifacts" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base shortcuts-builds" data-testid="nav-item-link" aria-label="Artifacts" data-track-action="click_menu_item" data-track-label="artifacts" data-track-property="nav_panel_project" data-qa-submenu-item="Artifacts"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Artifacts
      <!----></div>  <!----></a> <!----></li></ul></div></li><li><!----> <button id="menu-section-button-deploy" data-testid="menu-section-button" data-qa-section-name="Deploy" aria-controls="deploy" aria-expanded="false" data-qa-menu-item="Deploy" class="super-sidebar-nav-item gl-relative gl-mb-2 gl-flex gl-min-h-7 gl-w-full gl-appearance-none gl-items-center gl-gap-3 gl-rounded-base gl-border-0 gl-bg-transparent gl-px-3 gl-py-2 gl-text-left !gl-text-default !gl-no-underline focus:gl-focus"><span aria-hidden="true" class="gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-bg-transparent" style="width: 3px; border-radius: 3px; margin-right: 1px;"></span> <span class="gl-flex gl-w-6 gl-shrink-0"><svg data-testid="deployments-icon" role="img" aria-hidden="true" class="super-sidebar-nav-item-icon gl-m-auto gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#deployments"></use></svg></span> <span class="gl-truncate-end gl-grow gl-text-default">
      Deploy
    </span> <span class="gl-text-right gl-text-subtle"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="gl-animated-icon gl-animated-icon-off gl-animated-icon-current"><path d="M6.75 4.75L10 8L6.75 11.25" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="gl-animated-chevron-right-down-arrow"></path></svg></span></button> <!----> <div class="gl-m-0 gl-list-none gl-p-0 gl-duration-medium gl-ease-ease collapse" id="deploy" data-testid="menu-section" data-qa-section-name="Deploy" style="display: none;"><ul aria-label="Deploy" class="gl-m-0 gl-list-none gl-p-0"><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/releases" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base shortcuts-deployments-releases" data-testid="nav-item-link" aria-label="Releases" data-track-action="click_menu_item" data-track-label="releases" data-track-property="nav_panel_project" data-qa-submenu-item="Releases"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Releases
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/packages" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base shortcuts-container-registry" data-testid="nav-item-link" aria-label="Package registry" data-track-action="click_menu_item" data-track-label="packages_registry" data-track-property="nav_panel_project" data-qa-submenu-item="Package registry"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Package registry
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/container_registry" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base" data-testid="nav-item-link" aria-label="Container registry" data-track-action="click_menu_item" data-track-label="container_registry" data-track-property="nav_panel_project" data-qa-submenu-item="Container registry"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Container registry
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/ml/models" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base" data-testid="nav-item-link" aria-label="Model registry" data-track-action="click_menu_item" data-track-label="model_registry" data-track-property="nav_panel_project" data-qa-submenu-item="Model registry"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Model registry
      <!----></div>  <!----></a> <!----></li></ul></div></li><li><!----> <button id="menu-section-button-operate" data-testid="menu-section-button" data-qa-section-name="Operate" aria-controls="operate" aria-expanded="false" data-qa-menu-item="Operate" class="super-sidebar-nav-item gl-relative gl-mb-2 gl-flex gl-min-h-7 gl-w-full gl-appearance-none gl-items-center gl-gap-3 gl-rounded-base gl-border-0 gl-bg-transparent gl-px-3 gl-py-2 gl-text-left !gl-text-default !gl-no-underline focus:gl-focus"><span aria-hidden="true" class="gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-bg-transparent" style="width: 3px; border-radius: 3px; margin-right: 1px;"></span> <span class="gl-flex gl-w-6 gl-shrink-0"><svg data-testid="cloud-pod-icon" role="img" aria-hidden="true" class="super-sidebar-nav-item-icon gl-m-auto gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#cloud-pod"></use></svg></span> <span class="gl-truncate-end gl-grow gl-text-default">
      Operate
    </span> <span class="gl-text-right gl-text-subtle"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="gl-animated-icon gl-animated-icon-off gl-animated-icon-current"><path d="M6.75 4.75L10 8L6.75 11.25" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="gl-animated-chevron-right-down-arrow"></path></svg></span></button> <!----> <div class="gl-m-0 gl-list-none gl-p-0 gl-duration-medium gl-ease-ease collapse" id="operate" data-testid="menu-section" data-qa-section-name="Operate" style="display: none;"><ul aria-label="Operate" class="gl-m-0 gl-list-none gl-p-0"><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/environments" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base shortcuts-environments" data-testid="nav-item-link" aria-label="Environments" data-track-action="click_menu_item" data-track-label="environments" data-track-property="nav_panel_project" data-qa-submenu-item="Environments"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Environments
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/terraform_module_registry" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base" data-testid="nav-item-link" aria-label="Terraform modules" data-track-action="click_menu_item" data-track-label="infrastructure_registry" data-track-property="nav_panel_project" data-qa-submenu-item="Terraform modules"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Terraform modules
      <!----></div>  <!----></a> <!----></li></ul></div></li><li><!----> <button id="menu-section-button-monitor" data-testid="menu-section-button" data-qa-section-name="Monitor" aria-controls="monitor" aria-expanded="false" data-qa-menu-item="Monitor" class="super-sidebar-nav-item gl-relative gl-mb-2 gl-flex gl-min-h-7 gl-w-full gl-appearance-none gl-items-center gl-gap-3 gl-rounded-base gl-border-0 gl-bg-transparent gl-px-3 gl-py-2 gl-text-left !gl-text-default !gl-no-underline focus:gl-focus"><span aria-hidden="true" class="gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-bg-transparent" style="width: 3px; border-radius: 3px; margin-right: 1px;"></span> <span class="gl-flex gl-w-6 gl-shrink-0"><svg data-testid="monitor-icon" role="img" aria-hidden="true" class="super-sidebar-nav-item-icon gl-m-auto gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#monitor"></use></svg></span> <span class="gl-truncate-end gl-grow gl-text-default">
      Monitor
    </span> <span class="gl-text-right gl-text-subtle"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="gl-animated-icon gl-animated-icon-off gl-animated-icon-current"><path d="M6.75 4.75L10 8L6.75 11.25" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="gl-animated-chevron-right-down-arrow"></path></svg></span></button> <!----> <div class="gl-m-0 gl-list-none gl-p-0 gl-duration-medium gl-ease-ease collapse" id="monitor" data-testid="menu-section" data-qa-section-name="Monitor" style="display: none;"><ul aria-label="Monitor" class="gl-m-0 gl-list-none gl-p-0"><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/incidents" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base" data-testid="nav-item-link" aria-label="Incidents" data-track-action="click_menu_item" data-track-label="incidents" data-track-property="nav_panel_project" data-qa-submenu-item="Incidents"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Incidents
      <!----></div>  <!----></a> <!----></li></ul></div></li><li><!----> <button id="menu-section-button-analyze" data-testid="menu-section-button" data-qa-section-name="Analyze" aria-controls="analyze" aria-expanded="false" data-qa-menu-item="Analyze" class="super-sidebar-nav-item gl-relative gl-mb-2 gl-flex gl-min-h-7 gl-w-full gl-appearance-none gl-items-center gl-gap-3 gl-rounded-base gl-border-0 gl-bg-transparent gl-px-3 gl-py-2 gl-text-left !gl-text-default !gl-no-underline focus:gl-focus"><span aria-hidden="true" class="gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-bg-transparent" style="width: 3px; border-radius: 3px; margin-right: 1px;"></span> <span class="gl-flex gl-w-6 gl-shrink-0"><svg data-testid="chart-icon" role="img" aria-hidden="true" class="super-sidebar-nav-item-icon gl-m-auto gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#chart"></use></svg></span> <span class="gl-truncate-end gl-grow gl-text-default">
      Analyze
    </span> <span class="gl-text-right gl-text-subtle"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="gl-animated-icon gl-animated-icon-off gl-animated-icon-current"><path d="M6.75 4.75L10 8L6.75 11.25" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="gl-animated-chevron-right-down-arrow"></path></svg></span></button> <!----> <div class="gl-m-0 gl-list-none gl-p-0 gl-duration-medium gl-ease-ease collapse" id="analyze" data-testid="menu-section" data-qa-section-name="Analyze" style="display: none;"><ul aria-label="Analyze" class="gl-m-0 gl-list-none gl-p-0"><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/value_stream_analytics" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base shortcuts-project-cycle-analytics" data-testid="nav-item-link" aria-label="Value stream analytics" data-track-action="click_menu_item" data-track-label="cycle_analytics" data-track-property="nav_panel_project" data-qa-submenu-item="Value stream analytics"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Value stream analytics
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/graphs/master?ref_type=heads" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base" data-testid="nav-item-link" aria-label="Contributor analytics" data-track-action="click_menu_item" data-track-label="contributors" data-track-property="nav_panel_project" data-qa-submenu-item="Contributor analytics"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Contributor analytics
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/pipelines/charts" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base" data-testid="nav-item-link" aria-label="CI/CD analytics" data-track-action="click_menu_item" data-track-label="ci_cd_analytics" data-track-property="nav_panel_project" data-qa-submenu-item="CI/CD analytics"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      CI/CD analytics
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/graphs/master/charts" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base shortcuts-repository-charts" data-testid="nav-item-link" aria-label="Repository analytics" data-track-action="click_menu_item" data-track-label="repository_analytics" data-track-property="nav_panel_project" data-qa-submenu-item="Repository analytics"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Repository analytics
      <!----></div>  <!----></a> <!----></li><li data-testid="nav-item" class="show-on-focus-or-hover--context hide-on-focus-or-hover--context transition-opacity-on-hover--context gl-relative"><a href="https://gitlab.synchro.net/main/sbbs/-/ml/experiments" class="super-sidebar-nav-item show-on-focus-or-hover--control hide-on-focus-or-hover--control gl-relative gl-mb-1 gl-flex gl-min-h-7 gl-items-center gl-gap-3 gl-py-2 !gl-text-default !gl-no-underline focus:gl-focus gl-px-3 gl-rounded-base" data-testid="nav-item-link" aria-label="Model experiments" data-track-action="click_menu_item" data-track-label="model_experiments" data-track-property="nav_panel_project" data-qa-submenu-item="Model experiments"><div aria-hidden="true" data-testid="active-indicator" class="active-indicator gl-absolute gl-bottom-2 gl-left-2 gl-top-2 gl-transition-all gl-duration-slow gl-opacity-0" style="width: 3px; border-radius: 3px; margin-right: 1px;"></div> <div class="gl-flex gl-w-6 gl-shrink-0"><!----></div> <div data-testid="nav-item-link-label" class="gl-grow gl-text-default gl-break-anywhere">
      Model experiments
      <!----></div>  <!----></a> <!----></li></ul></div></li></ul></div> <div id="sidebar-portal-mount"></div> <div></div> <div class="bottom-scrim-wrapper"><div class="bottom-scrim"></div></div></div> <!----> <div class="gl-p-2"><div class="gl-disclosure-dropdown gl-new-dropdown"><div id="dropdown-toggle-btn-1" data-testid="base-dropdown-toggle" class="gl-new-dropdown-custom-toggle"><button data-testid="sidebar-help-button" type="button" class="btn super-sidebar-help-center-toggle btn-with-notification btn-default btn-md gl-button btn-default-tertiary"><!----> <svg data-testid="question-o-icon" role="img" aria-hidden="true" class="gl-button-icon gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#question-o"></use></svg>  <span class="gl-button-text"><!---->
      Help
    </span></button></div> <div id="base-dropdown-3" data-testid="base-dropdown-menu" class="gl-new-dropdown-panel !gl-w-31"><div class="gl-new-dropdown-arrow"></div> <div class="gl-new-dropdown-inner">  <ul id="disclosure-2" aria-labelledby="dropdown-toggle-btn-1" data-testid="disclosure-content" tabindex="-1" class="gl-new-dropdown-contents"> <!----> <li><!----> <ul class="gl-mb-0 gl-list-none gl-pl-0"><li tabindex="0" data-testid="disclosure-dropdown-item" class="gl-new-dropdown-item"><a href="https://gitlab.synchro.net/help" tabindex="-1" data-track-property="nav_help_menu" data-track-action="click_link" data-track-label="help" class="gl-new-dropdown-item-content"><span class="gl-new-dropdown-item-text-wrapper">
          Help
        </span></a></li><li tabindex="0" data-testid="disclosure-dropdown-item" class="gl-new-dropdown-item"><a href="https://about.gitlab.com/get-help/" tabindex="-1" data-track-property="nav_help_menu" data-track-action="click_link" data-track-label="support" class="gl-new-dropdown-item-content"><span class="gl-new-dropdown-item-text-wrapper">
          Support
        </span></a></li><li tabindex="0" data-testid="disclosure-dropdown-item" class="gl-new-dropdown-item"><a href="https://gitlab.synchro.net/help/docs" tabindex="-1" data-track-property="nav_help_menu" data-track-action="click_link" data-track-label="gitlab_documentation" class="gl-new-dropdown-item-content"><span class="gl-new-dropdown-item-text-wrapper">
          GitLab documentation
        </span></a></li><li tabindex="0" data-testid="disclosure-dropdown-item" class="gl-new-dropdown-item"><a href="https://about.gitlab.com/pricing" tabindex="-1" data-track-property="nav_help_menu" data-track-action="click_link" data-track-label="compare_gitlab_plans" class="gl-new-dropdown-item-content"><span class="gl-new-dropdown-item-text-wrapper">
          Compare GitLab plans
        </span></a></li><li tabindex="0" data-testid="disclosure-dropdown-item" class="gl-new-dropdown-item"><a href="https://forum.gitlab.com/" tabindex="-1" data-track-property="nav_help_menu" data-track-action="click_link" data-track-label="community_forum" class="gl-new-dropdown-item-content"><span class="gl-new-dropdown-item-text-wrapper">
          Community forum
        </span></a></li><li tabindex="0" data-testid="disclosure-dropdown-item" class="gl-new-dropdown-item"><a href="https://contributors.gitlab.com/" tabindex="-1" data-track-property="nav_help_menu" data-track-action="click_link" data-track-label="contribute_to_gitlab" class="gl-new-dropdown-item-content"><span class="gl-new-dropdown-item-text-wrapper">
          Contribute to GitLab
        </span></a></li><li tabindex="0" data-testid="disclosure-dropdown-item" class="gl-new-dropdown-item"><a href="https://about.gitlab.com/submit-feedback" tabindex="-1" data-track-property="nav_help_menu" data-track-action="click_link" data-track-label="submit_feedback" class="gl-new-dropdown-item-content"><span class="gl-new-dropdown-item-text-wrapper">
          Provide feedback
        </span></a></li></ul></li> <li class="gl-border-t gl-border-t-dropdown-divider gl-pt-2 gl-mt-2"><!----> <ul class="gl-mb-0 gl-list-none gl-pl-0"><li tabindex="0" data-testid="disclosure-dropdown-item" class="gl-new-dropdown-item"><button tabindex="-1" data-track-action="click_button" data-track-label="keyboard_shortcuts_help" data-track-property="nav_help_menu" type="button" class="gl-new-dropdown-item-content js-shortcuts-modal-trigger"><span class="gl-new-dropdown-item-text-wrapper"><span class="-gl-my-1 gl-flex gl-items-center gl-justify-between">
        Keyboard shortcuts
        <kbd aria-hidden="true" class="flat">?</kbd></span></span></button></li></ul></li></ul> </div></div></div> <!----> <div></div></div></div></nav> <a href="https://gitlab.synchro.net/explore/snippets" class="gl-hidden dashboard-shortcuts-snippets">
    Snippets
  </a><a href="https://gitlab.synchro.net/explore/groups" class="gl-hidden dashboard-shortcuts-groups">
    Groups
  </a><a href="https://gitlab.synchro.net/explore/projects/starred" class="gl-hidden dashboard-shortcuts-projects">
    Projects
  </a> <!----> <!----></div>


<div class="content-wrapper">
<div class="broadcast-wrapper">



</div>
<div class="alert-wrapper alert-wrapper-top-space gl-flex gl-flex-col gl-gap-3 container-fluid container-limited">

























</div>
<div class="top-bar-fixed container-fluid" data-testid="top-bar">
<div class="top-bar-container gl-flex gl-items-center gl-gap-2">
<div class="gl-grow gl-basis-0 gl-flex gl-items-center gl-justify-start gl-gap-3">
<button aria-controls="super-sidebar" aria-expanded="false" aria-label="Primary navigation sidebar" type="button" class="btn btn-default btn-md gl-button btn-default-tertiary btn-icon gl-button btn btn-icon btn-md btn-default btn-default-tertiary js-super-sidebar-toggle-expand super-sidebar-toggle -gl-ml-3"><!----> <svg data-testid="sidebar-icon" role="img" aria-hidden="true" class="gl-button-icon gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#sidebar"></use></svg>  <!----></button>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Main","item":"https://gitlab.synchro.net/main"},{"@type":"ListItem","position":2,"name":"Synchronet","item":"https://gitlab.synchro.net/main/sbbs"}]}


</script>
<div data-testid="breadcrumb-links" id="js-vue-page-breadcrumbs-wrapper">
<nav aria-label="Breadcrumb" class="gl-breadcrumbs" style=""><ol class="gl-breadcrumb-list breadcrumb"><!----> <li class="gl-breadcrumb-item gl-breadcrumb-item-sm"><a href="https://gitlab.synchro.net/main" class=""><img src="./synchronet sbbs zmodem_files/2020-05-27.png" alt="avatar" class="gl-breadcrumb-avatar-tile gl-border gl-mr-2 !gl-rounded-base gl-avatar gl-avatar-s16" aria-hidden="true" data-testid="avatar"><span class="gl-align-middle">Main</span></a></li><li class="gl-breadcrumb-item gl-breadcrumb-item-sm"><a href="https://gitlab.synchro.net/main/sbbs" aria-current="page" class=""><img src="./synchronet sbbs zmodem_files/2019-02-14.png" alt="avatar" class="gl-breadcrumb-avatar-tile gl-border gl-mr-2 !gl-rounded-base gl-avatar gl-avatar-s16" aria-hidden="true" data-testid="avatar"><span class="gl-align-middle">Synchronet</span></a></li></ol></nav>
<div id="js-injected-page-breadcrumbs"></div>
</div>


</div>
<div class="gl-flex-none gl-flex gl-items-center gl-justify-center gl-gap-3">
<div id="js-work-item-feedback"></div>

<!---->


</div>
</div>
</div>

<div class="container-fluid container-limited project-highlight-puc">
<main class="content" id="content-body" itemscope="" itemtype="http://schema.org/SoftwareSourceCode">
<div class="flash-container flash-container-page sticky" data-testid="flash-container">
<!---->
</div>










<header class="project-home-panel js-show-on-project-root gl-mt-5 hidden">
<div class="gl-flex gl-justify-between gl-flex-wrap gl-flex-col md:gl-flex-row gl-gap-5">
<div class="home-panel-title-row gl-flex gl-items-center">
<img srcset="/uploads/-/system/project/avatar/13/2019-02-14.png?width=48 1x, /uploads/-/system/project/avatar/13/2019-02-14.png?width=96 2x" alt="Synchronet" class="gl-avatar gl-avatar-s48 gl-self-start gl-shrink-0 gl-mr-4 !gl-rounded-base" height="48" width="48" loading="lazy" itemprop="image" src="./synchronet sbbs zmodem_files/2019-02-14(1).png">

<h1 class="home-panel-title gl-heading-1 gl-flex gl-items-center gl-flex-wrap gl-gap-3 gl-break-anywhere gl-mb-0" data-testid="project-name-content" itemprop="name">
Synchronet
<button class="has-tooltip gl-border-0 gl-bg-transparent gl-p-0 gl-leading-0 gl-text-inherit visibility-icon gl-inline-flex" data-container="body" data-placement="top" title="Public - The project can be accessed without any authentication." type="button" aria-label="Public - The project can be accessed without any authentication."><svg class="s16 gl-fill-icon-subtle" data-testid="earth-icon"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#earth"></use></svg></button>


</h1>
</div>
<div class="gl-justify-content-md-end project-repo-buttons gl-flex gl-flex-wrap gl-items-center gl-gap-3"><!----> <!----> <div role="group" class="gl-button-group btn-group"><a data-testid="star-button" title="You must sign in to star a project" href="https://gitlab.synchro.net/users/sign_in?redirect_to_referer=yes" class="btn star-btn btn-default btn-md gl-button"><!----> <!---->  <span class="gl-button-text"><svg data-testid="star-o-icon" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#star-o"></use></svg>
    Star
  </span></a> <a data-testid="star-count" title="Starrers" href="https://gitlab.synchro.net/main/sbbs/-/starrers" class="btn star-count btn-default btn-md gl-button"><!----> <!---->  <span class="gl-button-text">
    20
  </span></a></div> <!----> <span itemprop="identifier" data-testid="project-id-content" class="gl-sr-only">
      Project ID: 13
    </span> <div class="gl-disclosure-dropdown gl-relative gl-w-full sm:gl-w-auto gl-new-dropdown" data-testid="groups-projects-more-actions-dropdown"><div id="dropdown-toggle-btn-14" data-testid="base-dropdown-toggle" class="gl-new-dropdown-custom-toggle"><div class="gl-min-h-7"><button aria-label="More actions" title="More actions" type="button" class="btn gl-new-dropdown-toggle gl-absolute gl-left-0 gl-top-0 gl-w-full sm:gl-w-auto md:!gl-hidden btn-default btn-md gl-button btn-default-secondary"><!----> <!---->  <span class="gl-button-text gl-w-full"><span class="gl-new-dropdown-button-text">More actions</span> <svg data-testid="chevron-down-icon" role="img" aria-hidden="true" class="dropdown-chevron gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#chevron-down"></use></svg></span></button> <button aria-label="More actions" title="More actions" type="button" class="btn gl-new-dropdown-toggle gl-new-dropdown-icon-only gl-new-dropdown-toggle-no-caret gl-hidden md:!gl-flex btn-default btn-md gl-button btn-default-tertiary btn-icon"><!----> <svg data-testid="ellipsis_v-icon" role="img" aria-hidden="true" class="gl-button-icon gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#ellipsis_v"></use></svg>  <!----></button></div></div> <div id="base-dropdown-16" data-testid="base-dropdown-menu" class="gl-new-dropdown-panel !gl-w-31"><div class="gl-new-dropdown-arrow"></div> <div class="gl-new-dropdown-inner">  <ul id="disclosure-15" aria-labelledby="dropdown-toggle-btn-14" data-testid="disclosure-content" tabindex="-1" class="gl-new-dropdown-contents"> <li tabindex="0" data-testid="disclosure-dropdown-item" class="gl-new-dropdown-item" data-clipboard-text="13"><button tabindex="-1" data-testid="copy-project-id" type="button" class="gl-new-dropdown-item-content"><span class="gl-new-dropdown-item-text-wrapper">
          Copy project ID: 13
        </span></button></li> <!----> <!----></ul> </div></div></div></div>
</div>

</header>

<div class="project-page-indicator js-show-on-project-root hidden"></div>
<div class="project-page-layout">
<div class="project-page-layout-sidebar js-show-on-project-root gl-mt-5 hidden">
<aside class="project-page-sidebar" data-testid="project-page-sidebar">
<div class="project-page-sidebar-block home-panel-home-desc gl-py-4 gl-border-b gl-border-b-subtle !gl-pt-2">
<h2 class="gl-text-base gl-font-bold gl-leading-reset gl-text-heading gl-m-0 gl-mb-1">Project information</h2>
<div class="home-panel-description gl-break-words">
<div class="home-panel-description-markdown read-more-container" data-read-more-height="320" itemprop="description" style="--read-more-height: 320px;">
<div class="read-more-content">
<p data-sourcepos="1:1-1:67" dir="auto">Synchronet source code, documentation and versioned run-time files.</p>
</div>

</div>
</div>
<div class="gl-mb-2">
<div class="progress repository-languages-bar js-show-on-project-root hidden"><div class="progress-bar has-tooltip" style="width: 64.82%; background-color:#555555" data-html="true" title="&lt;span class=&quot;repository-language-bar-tooltip-language&quot;&gt;C&lt;/span&gt;&amp;nbsp;&lt;span class=&quot;repository-language-bar-tooltip-share&quot;&gt;64.8%&lt;/span&gt;"></div><div class="progress-bar has-tooltip" style="width: 22.42%; background-color:#f1e05a" data-html="true" title="&lt;span class=&quot;repository-language-bar-tooltip-language&quot;&gt;JavaScript&lt;/span&gt;&amp;nbsp;&lt;span class=&quot;repository-language-bar-tooltip-share&quot;&gt;22.4%&lt;/span&gt;"></div><div class="progress-bar has-tooltip" style="width: 5.5%; background-color:#f34b7d" data-html="true" title="&lt;span class=&quot;repository-language-bar-tooltip-language&quot;&gt;C++&lt;/span&gt;&amp;nbsp;&lt;span class=&quot;repository-language-bar-tooltip-share&quot;&gt;5.5%&lt;/span&gt;"></div><div class="progress-bar has-tooltip" style="width: 4.53%; background-color:#E3F171" data-html="true" title="&lt;span class=&quot;repository-language-bar-tooltip-language&quot;&gt;Pascal&lt;/span&gt;&amp;nbsp;&lt;span class=&quot;repository-language-bar-tooltip-share&quot;&gt;4.5%&lt;/span&gt;"></div><div class="progress-bar has-tooltip" style="width: 1.63%; background-color:#e34c26" data-html="true" title="&lt;span class=&quot;repository-language-bar-tooltip-language&quot;&gt;HTML&lt;/span&gt;&amp;nbsp;&lt;span class=&quot;repository-language-bar-tooltip-share&quot;&gt;1.6%&lt;/span&gt;"></div></div>
</div>
</div>
<div class="project-page-sidebar-block gl-py-4 gl-border-b gl-border-b-subtle">
<nav class="project-stats">
<ul class="nav gl-gap-y-2 gl-gap-x-5">
<li class="nav-item">
<a class="nav-link stat-link !gl-px-0 !gl-pb-2" href="https://gitlab.synchro.net/main/sbbs/-/commits/master"><svg class="s16 gl-fill-icon-subtle gl-mr-3" data-testid="commit-icon"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#commit"></use></svg><strong class="project-stat-value">37,190</strong> Commits</a>
</li>
<li class="nav-item">
<a class="nav-link stat-link !gl-px-0 !gl-pb-2" href="https://gitlab.synchro.net/main/sbbs/-/branches"><svg class="s16 gl-fill-icon-subtle gl-mr-3" data-testid="branch-icon"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#branch"></use></svg><strong class="project-stat-value">31</strong> Branches</a>
</li>
<li class="nav-item">
<a class="nav-link stat-link !gl-px-0 !gl-pb-2" href="https://gitlab.synchro.net/main/sbbs/-/tags"><svg class="s16 gl-fill-icon-subtle gl-mr-3" data-testid="label-icon"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#label"></use></svg><strong class="project-stat-value">70</strong> Tags</a>
</li>
<li class="nav-item">
<a class="nav-link stat-link !gl-px-0 !gl-pb-2" href="https://gitlab.synchro.net/main/sbbs/-/releases"><svg class="s16 gl-fill-icon-subtle gl-mr-3" data-testid="rocket-launch-icon"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#rocket-launch"></use></svg><strong class="project-stat-value">4</strong> Releases</a>
</li>
</ul>

</nav>
</div>
<div class="project-page-sidebar-block gl-py-4 gl-border-b gl-border-b-subtle">
<div class="project-buttons gl-mb-2 js-show-on-project-root hidden" data-testid="project-buttons">
<ul class="nav gl-gap-y-2 gl-gap-x-5">
<li class="nav-item">
<a class="nav-link stat-link !gl-px-0 !gl-pb-2 btn-default" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/README.md"><svg class="s16 gl-fill-icon-subtle gl-mr-3" data-testid="doc-text-icon"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#doc-text"></use></svg>README</a>
</li>
<li class="nav-item">
<a class="nav-link stat-link !gl-px-0 !gl-pb-2 btn-default" itemprop="license" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/LICENSE"><svg class="s16 gl-fill-icon-subtle gl-mr-3" data-testid="scale-icon"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#scale"></use></svg><span class="project-stat-value">LICENSE</span></a>
</li>
<li class="nav-item">
<a class="nav-link stat-link !gl-px-0 !gl-pb-2 btn-default" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/CONTRIBUTING.md"><svg class="s16 gl-fill-icon-subtle gl-mr-3" data-testid="doc-text-icon"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#doc-text"></use></svg>CONTRIBUTING</a>
</li>
</ul>

</div>
</div>

<div class="project-page-sidebar-block gl-py-4">
<p class="gl-font-bold gl-text-strong gl-m-0 gl-mb-1">Created on</p>
<span>August 16, 2020</span>
</div>
</aside>

</div>
<div class="project-page-layout-content">
<div class="project-show-files">
<div class="tree-holder clearfix js-per-page gl-mt-5" data-blame-per-page="1000" id="tree-holder">
<section class=""><div class="tree-ref-container mb-2 mb-md-0 gl-flex gl-flex-wrap gl-gap-5"><div class="tree-ref-holder gl-max-w-26"><div class="ref-selector gl-w-full gl-new-dropdown !gl-block" data-testid="ref-dropdown-container"><button id="dropdown-toggle-btn-18" data-testid="base-dropdown-toggle" aria-haspopup="listbox" aria-expanded="false" aria-controls="base-dropdown-20" type="button" class="btn btn-default btn-md btn-block gl-button gl-font-monospace gl-mb-0 gl-new-dropdown-toggle"><!----> <svg data-testid="branch-icon" role="img" aria-hidden="true" class="gl-button-icon gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#branch"></use></svg>  <span class="gl-button-text gl-w-full"><span class="gl-new-dropdown-button-text">
        master
      </span> <svg data-testid="chevron-down-icon" role="img" aria-hidden="true" class="gl-button-icon gl-new-dropdown-chevron gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#chevron-down"></use></svg></span></button> <div id="base-dropdown-20" data-testid="base-dropdown-menu" class="gl-new-dropdown-panel !gl-w-31"><div class="gl-new-dropdown-arrow"></div> <div class="gl-new-dropdown-inner"> <div class="gl-flex gl-min-h-8 gl-items-center !gl-p-4 gl-border-b-1 gl-border-b-solid gl-border-b-dropdown-divider"><div id="listbox-header-19" data-testid="listbox-header-text" class="gl-grow gl-pr-2 gl-text-sm gl-font-bold gl-text-strong">
      Select Git revision
    </div> <!----> <!----></div> <div class="gl-border-b-1 gl-border-b-solid gl-border-b-dropdown-divider"><div class="gl-listbox-search" data-testid="listbox-search-input"><svg data-testid="search-sm-icon" role="img" aria-hidden="true" class="gl-listbox-search-icon gl-icon s12 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#search-sm"></use></svg> <input type="search" aria-label="Search by Git revision" placeholder="Search by Git revision" class="gl-listbox-search-input"> <!----></div> <!----></div> <div id="listbox-17" aria-labelledby="listbox-header-19" role="listbox" tabindex="0" class="gl-new-dropdown-contents gl-new-dropdown-contents-with-scrim-overlay gl-new-dropdown-contents"><div aria-hidden="true" data-testid="top-scrim" class="top-scrim-wrapper"><div class="top-scrim top-scrim-dark"></div></div> <div aria-hidden="true"></div> <ul role="group" aria-labelledby="gl-listbox-group-55" class="gl-mb-0 gl-pl-0"><li id="gl-listbox-group-55" role="presentation" class="gl-pb-2 gl-pl-4 gl-pt-3 gl-text-sm gl-font-bold gl-text-strong">
      Branches <span class="gl-badge badge badge-pill badge-muted"><!----> <span class="gl-badge-content">20</span></span></li>  <li role="option" tabindex="-1" aria-selected="true" class="gl-new-dropdown-item" data-testid="listbox-item-refs/heads/master"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      master
      <span class="gl-badge badge badge-pill badge-info"><!----> <span class="gl-badge-content">default</span></span> <span class="gl-badge badge badge-pill badge-neutral" title="" size="sm"><!----> <span class="gl-badge-content">
  protected
</span></span></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/heads/dailybuild_linux-x64"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      dailybuild_linux-x64
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/heads/dailybuild_win32"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      dailybuild_win32
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/heads/dailybuild_macos-armv8"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      dailybuild_macos-armv8
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/heads/syncterm-1.7"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      syncterm-1.7
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/heads/dd_msg_scan_config"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      dd_msg_scan_config
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/heads/dd_lightbar_menu_improve_utf8_item_printing"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      dd_lightbar_menu_improve_utf8_item_printing
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/heads/sqlite"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      sqlite
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/heads/rip_abstraction"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      rip_abstraction
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/heads/dd_file_lister_filanem_in_desc_color"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      dd_file_lister_filanem_in_desc_color
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/heads/mode7"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      mode7
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/heads/dd_msg_reader_are_you_there_warning_improvement"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      dd_msg_reader_are_you_there_warning_improvement
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/heads/c23-playing"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      c23-playing
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/heads/syncterm-1.3"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      syncterm-1.3
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/heads/syncterm-1.2"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      syncterm-1.2
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/heads/test-build"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      test-build
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/heads/hide_remote_connection_with_telgate"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      hide_remote_connection_with_telgate
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/heads/638-can-t-control-c-during-a-file-search"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      638-can-t-control-c-during-a-file-search
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/heads/add_body_to_pager_email"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      add_body_to_pager_email
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/heads/mingw32-build"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      mingw32-build
      <!----> <!----></span></span></li></ul><ul role="group" aria-labelledby="gl-listbox-group-56" class="gl-mb-0 gl-pl-0 gl-border-t-1 gl-border-t-solid gl-border-t-dropdown-divider gl-pt-1 gl-mt-2"><li id="gl-listbox-group-56" role="presentation" class="gl-pb-2 gl-pl-4 gl-pt-3 gl-text-sm gl-font-bold gl-text-strong">
      Tags <span class="gl-badge badge badge-pill badge-muted"><!----> <span class="gl-badge-content">20</span></span></li>  <li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/tags/syncterm-1.7"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      syncterm-1.7
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/tags/syncterm-1.7rc1"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      syncterm-1.7rc1
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/tags/sbbs320d"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      sbbs320d
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/tags/syncterm-1.6"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      syncterm-1.6
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/tags/syncterm-1.5"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      syncterm-1.5
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/tags/syncterm-1.4"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      syncterm-1.4
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/tags/sbbs320b"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      sbbs320b
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/tags/syncterm-1.3"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      syncterm-1.3
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/tags/syncterm-1.2"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      syncterm-1.2
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/tags/syncterm-1.2rc6"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      syncterm-1.2rc6
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/tags/syncterm-1.2rc5"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      syncterm-1.2rc5
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/tags/push"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      push
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/tags/syncterm-1.2rc4"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      syncterm-1.2rc4
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/tags/syncterm-1.2rc2"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      syncterm-1.2rc2
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/tags/syncterm-1.2rc1"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      syncterm-1.2rc1
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/tags/sbbs319b"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      sbbs319b
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/tags/sbbs318b"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      sbbs318b
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/tags/goodbuild_linux-x64_Sep-01-2020"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      goodbuild_linux-x64_Sep-01-2020
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/tags/goodbuild_win32_Sep-01-2020"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      goodbuild_win32_Sep-01-2020
      <!----> <!----></span></span></li><li role="option" tabindex="-1" class="gl-new-dropdown-item" data-testid="listbox-item-refs/tags/goodbuild_linux-x64_Aug-31-2020"><span class="gl-new-dropdown-item-content"><svg data-testid="dropdown-item-checkbox" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current gl-new-dropdown-item-check-icon gl-invisible gl-mt-3 gl-self-start"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#mobile-issue-close"></use></svg> <span class="gl-new-dropdown-item-text-wrapper">
      goodbuild_linux-x64_Aug-31-2020
      <!----> <!----></span></span></li></ul> <!----> <!----> <div aria-hidden="true"></div> <div aria-hidden="true" data-testid="bottom-scrim" class="bottom-scrim-wrapper"><div class="bottom-scrim !gl-rounded-none"></div></div></div> <span data-testid="listbox-number-of-results" aria-live="assertive" class="gl-sr-only">
      40 results
    </span>  </div></div></div> <!----></div> <nav aria-label="Files breadcrumb" data-current-path="src/sbbs3" class="js-repo-breadcrumbs gl-flex js-repo-breadcrumbs"><ol class="breadcrumb repo-breadcrumb"><li class="breadcrumb-item"><a href="https://gitlab.synchro.net/main/sbbs/-/tree/master?ref_type=heads" class="gl-link"><span>sbbs</span></a></li><li class="breadcrumb-item"><a href="https://gitlab.synchro.net/main/sbbs/-/tree/master/src?ref_type=heads" class="gl-link"><span>src</span></a></li><li class="breadcrumb-item"><a href="https://gitlab.synchro.net/main/sbbs/-/tree/master/src/sbbs3?ref_type=heads" class="gl-link"><span>sbbs3</span></a></li><li class="breadcrumb-item"><a href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads" aria-current="page" class="router-link-exact-active router-link-active gl-link"><strong>zmodem.c</strong></a></li> <!----></ol> <!----> <!----></nav></div> <div class="gl-flex gl-flex-col gl-items-stretch gl-justify-end sm:gl-flex-row sm:gl-items-center sm:gl-gap-5 gl-my-5"><h1 data-testid="repository-heading" class="gl-mt-0 gl-inline-flex gl-flex-1 gl-items-center gl-gap-3 gl-break-words gl-text-size-h1 sm:gl-my-0"><span aria-hidden="true" class="gl-inline-flex"><svg class="s16"><use href="/assets/file_icons/file_icons-88a95467170997d6a4052c781684c8250847147987090747773c1ee27c513c5f.svg#c"></use></svg></span>zmodem.c
      <!----></h1> <!----> <div data-testid="blob-controls" class="gl-flex gl-flex-wrap gl-items-center gl-gap-3 gl-self-end"><!----> <button aria-keyshortcuts="t" data-testid="find" type="button" class="btn btn-default btn-md gl-button sm:gl-w-auto gl-w-full sm:gl-mt-0 gl-mt-3 gl-hidden sm:gl-inline-flex"><!----> <!---->  <span class="gl-button-text">
    Find file
  </span></button> <a data-testid="blame" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads" class="btn js-blob-blame-link btn-default btn-md gl-button sm:gl-w-auto gl-w-full sm:gl-mt-0 gl-mt-3 gl-hidden sm:gl-inline-flex"><!----> <!---->  <span class="gl-button-text">
    Blame
  </span></a> <!----> <div class="!gl-m-0 sm:gl-ml-3" project-path="main/sbbs" project-id="13"><div class="gl-disclosure-dropdown gl-new-dropdown !gl-block" aria-label="" data-testid="action-dropdown"><button id="dropdown-toggle-btn-133" data-testid="base-dropdown-toggle" aria-expanded="false" aria-controls="base-dropdown-135" type="button" class="btn btn-confirm btn-md btn-block gl-button gl-new-dropdown-toggle"><!----> <!---->  <span class="gl-button-text gl-w-full"><span class="gl-new-dropdown-button-text">
        Edit
      </span> <svg data-testid="chevron-down-icon" role="img" aria-hidden="true" class="gl-button-icon gl-new-dropdown-chevron gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#chevron-down"></use></svg></span></button> <div id="base-dropdown-135" data-testid="base-dropdown-menu" class="gl-new-dropdown-panel"><div class="gl-new-dropdown-arrow"></div> <div class="gl-new-dropdown-inner">  <ul id="disclosure-134" aria-labelledby="dropdown-toggle-btn-133" data-testid="disclosure-content" tabindex="-1" class="gl-new-dropdown-contents"> <li class="edit-dropdown-group-width"><!----> <ul class="gl-mb-0 gl-list-none gl-pl-0"><li tabindex="0" data-testid="webide-menu-item" class="gl-new-dropdown-item"><button tabindex="-1" type="button" class="gl-new-dropdown-item-content"><span class="gl-new-dropdown-item-text-wrapper"><div class="gl-flex gl-flex-col"><span class="gl-mb-2 gl-flex gl-items-center gl-justify-between"><span data-testid="action-primary-text" class="gl-font-bold">Open in Web IDE</span> <kbd class="flat">.</kbd></span> <span data-testid="action-secondary-text" class="gl-text-sm gl-text-subtle">
              Quickly and easily edit multiple files in your project.
            </span></div></span></button></li><li tabindex="0" data-testid="edit-menu-item" class="gl-new-dropdown-item"><a href="https://gitlab.synchro.net/main/sbbs/-/edit/master/src/sbbs3/zmodem.c?ref_type=heads" tabindex="-1" class="gl-new-dropdown-item-content"><span class="gl-new-dropdown-item-text-wrapper"><div class="gl-flex gl-flex-col"><span class="gl-mb-2 gl-flex gl-items-center gl-justify-between"><span data-testid="action-primary-text" class="gl-font-bold">Edit single file</span> <!----></span> <span data-testid="action-secondary-text" class="gl-text-sm gl-text-subtle">
              Edit this file only.
            </span></div></span></a></li></ul></li> </ul> </div></div></div> <!----></div> <!----> <div class="gl-disclosure-dropdown gl-mr-0 gl-new-dropdown" data-testid="blob-overflow-menu"><button id="dropdown-toggle-btn-145" data-testid="base-dropdown-toggle" aria-expanded="false" aria-controls="base-dropdown-147" type="button" class="btn btn-default btn-md gl-button btn-default-tertiary gl-new-dropdown-toggle gl-new-dropdown-icon-only btn-icon gl-new-dropdown-toggle-no-caret"><!----> <svg data-testid="ellipsis_v-icon" role="img" aria-hidden="true" class="gl-button-icon gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#ellipsis_v"></use></svg>  <span class="gl-button-text"><span class="gl-new-dropdown-button-text gl-sr-only">
        File actions
      </span> <!----></span></button> <div id="base-dropdown-147" data-testid="base-dropdown-menu" class="gl-new-dropdown-panel !gl-w-31"><div class="gl-new-dropdown-arrow"></div> <div class="gl-new-dropdown-inner">  <div id="disclosure-146" aria-labelledby="dropdown-toggle-btn-145" data-testid="disclosure-content" tabindex="-1" class="gl-new-dropdown-contents"><li><!----> <ul class="gl-mb-0 gl-list-none gl-pl-0"><li tabindex="0" data-testid="find" class="sm:gl-hidden gl-new-dropdown-item" aria-keyshortcuts="t"><button tabindex="-1" type="button" class="gl-new-dropdown-item-content"><span class="gl-new-dropdown-item-text-wrapper"><span class="gl-flex gl-items-center gl-justify-between"><span>Find file</span> <kbd class="flat">t</kbd></span></span></button></li> <li tabindex="0" data-testid="blame-dropdown-item" class="js-blob-blame-link sm:gl-hidden gl-new-dropdown-item"><a href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads" tabindex="-1" data-testid="blame" class="gl-new-dropdown-item-content"><span class="gl-new-dropdown-item-text-wrapper">
          Blame
        </span></a></li> <li tabindex="0" data-testid="permalink" class="gl-new-dropdown-item" aria-keyshortcuts="y" data-clipboard-text="https://gitlab.synchro.net/main/sbbs/-/blob/5eca818f97d108fe86f199dbca20e25b5a030863/src/sbbs3/zmodem.c" data-clipboard-handle-tooltip="false"><button tabindex="-1" type="button" class="gl-new-dropdown-item-content"><span class="gl-new-dropdown-item-text-wrapper"><span class="gl-flex gl-items-center gl-justify-between"><span>Copy permalink</span> <kbd class="flat">y</kbd></span></span></button></li></ul></li> <!----> <li class="sm:gl-hidden gl-border-t gl-border-t-dropdown-divider gl-pt-2 gl-mt-2"><!----> <ul class="gl-mb-0 gl-list-none gl-pl-0"><li tabindex="0" data-testid="copy-item" class="js-copy-blob-source-btn gl-new-dropdown-item"><button tabindex="-1" data-testid="copy-contents-button" type="button" class="gl-new-dropdown-item-content"><span class="gl-new-dropdown-item-text-wrapper">
          Copy contents
        </span></button></li> <li tabindex="0" data-testid="open-raw-item" class="gl-new-dropdown-item"><a target="_blank" href="https://gitlab.synchro.net/main/sbbs/-/raw/master/src/sbbs3/zmodem.c?ref_type=heads" tabindex="-1" class="gl-new-dropdown-item-content" rel="noopener noreferrer"><span class="gl-new-dropdown-item-text-wrapper">
          Open raw
        </span></a></li> <li tabindex="0" data-testid="disclosure-dropdown-item" class="gl-new-dropdown-item" data-test="download-item"><a target="_blank" href="https://gitlab.synchro.net/main/sbbs/-/raw/master/src/sbbs3/zmodem.c?ref_type=heads&amp;inline=false" tabindex="-1" data-testid="download-button" class="gl-new-dropdown-item-content" rel="noopener noreferrer"><span class="gl-new-dropdown-item-text-wrapper">
          Download
        </span></a></li> <!----></ul></li> <!----></div> </div></div></div></div></div></section>
<div class="info-well project-last-commit gl-flex-col gl-mt-5">
<div><div class="well-segment commit gl-flex gl-w-full !gl-px-5 !gl-py-4 gl-hidden sm:gl-flex"><a href="https://gitlab.synchro.net/rswindell" data-username="" class="gl-avatar-link user-avatar-link js-user-link gl-my-2 gl-mr-3 gl-link gl-link-meta"><span class=""><img src="./synchronet sbbs zmodem_files/avatar.png" alt="Rob Swindell (on Windows 11)&#39;s avatar" class="gl-bg-cover gl-avatar gl-avatar-circle gl-avatar-s32" data-src="/uploads/-/system/user/avatar/1/avatar.png?width=64" data-testid="user-avatar-image"> <!----></span> <!----> </a> <div class="commit-detail flex-list gl-flex gl-min-w-0 gl-grow"><div data-testid="commit-content" class="commit-content gl-inline-flex gl-w-full gl-flex-wrap gl-items-baseline"><div class="gl-inline-flex gl-basis-full gl-items-center gl-gap-x-3"><a href="https://gitlab.synchro.net/main/sbbs/-/commit/ab995dd1db4530b0f3bd90ab85ae393f49aabbc2" class="commit-row-message item-title gl-line-clamp-1 gl-whitespace-normal !gl-break-all gl-link">Fix parity inversion in comments</a> <button title="Toggle commit description" aria-label="Toggle commit description" type="button" class="btn !gl-ml-0 btn-default btn-md gl-button btn-icon button-ellipsis-horizontal"><!----> <svg data-testid="ellipsis_h-icon" role="img" aria-hidden="true" class="gl-button-icon gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#ellipsis_h"></use></svg>  <!----></button></div> <div data-testid="committer" class="committer gl-basis-full gl-truncate gl-text-sm"><a href="https://gitlab.synchro.net/rswindell" class="commit-author-link js-user-link gl-link">
          Rob Swindell</a>
        authored
        <time title="December 2, 2025 at 5:48:36 PM EST" datetime="2025-12-02T14:48:36-08:00" class="">2 days ago</time></div> <pre class="commit-row-description gl-mb-3 gl-whitespace-pre-wrap">Even parity means that the high bit is *set* (when necessary) to insure an
even number of set bits in every sent byte. Odd parity is the opposite.
I had this backwards in my comments.</pre></div> <div class="gl-grow"></div> <div class="commit-actions gl-my-2 gl-flex gl-items-start gl-gap-3"><!----> <!----> <div role="group" class="js-commit-sha-group gl-ml-4 gl-flex gl-items-center gl-button-group btn-group"><span variant="default" size="md" data-testid="last-commit-id-label" class="gl-font-monospace dark:!gl-bg-strong gl-button btn btn-label btn-md"><!----> <!---->  <span class="gl-button-text">ab995dd1</span></span> <button id="clipboard-button-144" title="Copy commit SHA" data-clipboard-text="ab995dd1db4530b0f3bd90ab85ae393f49aabbc2" data-clipboard-handle-tooltip="false" aria-label="Copy commit SHA" aria-live="polite" type="button" class="btn input-group-text dark:!gl-border-l-section btn-default btn-md gl-button btn-default-secondary btn-icon"><!----> <svg data-testid="copy-to-clipboard-icon" role="img" aria-hidden="true" class="gl-button-icon gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#copy-to-clipboard"></use></svg>  <!----></button></div> <a data-testid="last-commit-history" href="https://gitlab.synchro.net/main/sbbs/-/commits/master/src/sbbs3/zmodem.c?ref_type=heads" class="btn !gl-ml-0 btn-default btn-md gl-button btn-default-secondary"><!----> <!---->  <span class="gl-button-text">
        History
      </span></a></div></div> <!----></div> <div class="well-segment !gl-px-4 !gl-py-3 gl-block !gl-border-t-0 sm:gl-hidden"><div class="gl-flex gl-flex-wrap gl-items-center gl-justify-between"><div class="gl-flex gl-items-center gl-gap-3 gl-text-sm"><a href="https://gitlab.synchro.net/rswindell" data-username="" class="gl-avatar-link user-avatar-link js-user-link gl-link gl-link-meta"><span class=""><img src="./synchronet sbbs zmodem_files/avatar.png" alt="Rob Swindell (on Windows 11)&#39;s avatar" class="gl-bg-cover gl-avatar gl-avatar-circle gl-avatar-s32" data-src="/uploads/-/system/user/avatar/1/avatar.png?width=64" data-testid="user-avatar-image"> <!----></span> <!----> </a> <a href="https://gitlab.synchro.net/main/sbbs/-/commit/ab995dd1db4530b0f3bd90ab85ae393f49aabbc2" class="commit-row-message item-title gl-line-clamp-1 gl-whitespace-normal !gl-break-all gl-link"><svg data-testid="commit-icon" role="img" aria-hidden="true" class="gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#commit"></use></svg>
        ab995dd1
      </a> <time title="December 2, 2025 at 5:48:36 PM EST" datetime="2025-12-02T14:48:36-08:00" class="gl-text-subtle">2 days ago</time></div> <div class="gl-flex gl-items-center gl-gap-3"><button title="Toggle commit description" aria-label="Toggle commit description" data-testid="text-expander" type="button" class="btn text-expander btn-default btn-md gl-button btn-icon button-ellipsis-horizontal"><!----> <svg data-testid="ellipsis_h-icon" role="img" aria-hidden="true" class="gl-button-icon gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#ellipsis_h"></use></svg>  <!----></button> <a data-testid="collapsible-commit-history" href="https://gitlab.synchro.net/main/sbbs/-/commits/master/src/sbbs3/zmodem.c?ref_type=heads" class="btn btn-default btn-sm gl-button"><!----> <!---->  <span class="gl-button-text">
        History
      </span></a></div></div> <!----></div></div>
</div>
<div class="gl-relative"><!----> <div id="fileHolder" class="file-holder"><div class="js-file-title file-title-flex-parent" is-blob-page=""><div class="gl-mb-3 gl-flex gl-gap-3 md:gl-mb-0"><!----> <div class="file-header-content gl-flex gl-items-center gl-leading-1"> <span aria-hidden="true"><svg class="s16 gl-mr-3"><use href="/assets/file_icons/file_icons-88a95467170997d6a4052c781684c8250847147987090747773c1ee27c513c5f.svg#c"></use></svg></span> <strong data-testid="file-title-content" class="file-title-name js-blob-header-filepath gl-mr-1 gl-break-all gl-font-bold gl-text-strong">zmodem.c</strong> <button id="clipboard-button-143" title="Copy file path" data-clipboard-text="{&quot;text&quot;:&quot;src/sbbs3/zmodem.c&quot;,&quot;gfm&quot;:&quot;`src/sbbs3/zmodem.c`&quot;}" data-clipboard-handle-tooltip="false" aria-label="Copy file path" aria-live="polite" type="button" class="btn btn-default btn-md gl-button btn-default-tertiary btn-icon gl-mr-2"><!----> <svg data-testid="copy-to-clipboard-icon" role="img" aria-hidden="true" class="gl-button-icon gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#copy-to-clipboard"></use></svg>  <!----></button> <small class="gl-mr-3 gl-text-subtle">61.68 KiB</small> <!----></div></div> <div class="file-actions gl-flex gl-flex-wrap gl-gap-3"><div role="group" class="js-blob-viewer-switcher gl-button-group btn-group"></div> <!---->  <!---->  <div role="group" class="gl-button-group btn-group gl-hidden sm:gl-inline-flex" data-testid="default-actions-container"><button aria-label="Copy file contents" title="Copy file contents" data-testid="copy-contents-button" type="button" class="btn js-copy-blob-source-btn btn-default btn-md gl-button btn-icon"><!----> <svg data-testid="copy-to-clipboard-icon" role="img" aria-hidden="true" class="gl-button-icon gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#copy-to-clipboard"></use></svg>  <!----></button> <a aria-label="Open raw" title="Open raw" href="https://gitlab.synchro.net/main/sbbs/-/raw/master/src/sbbs3/zmodem.c?ref_type=heads" rel="noopener noreferrer" target="_blank" class="btn btn-default btn-md gl-button btn-icon"><!----> <svg data-testid="doc-code-icon" role="img" aria-hidden="true" class="gl-button-icon gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#doc-code"></use></svg>  <!----></a> <a aria-label="Download" title="Download" data-testid="download-button" href="https://gitlab.synchro.net/main/sbbs/-/raw/master/src/sbbs3/zmodem.c?ref_type=heads&amp;inline=false" rel="noopener noreferrer" target="_blank" class="btn btn-default btn-md gl-button btn-icon"><!----> <svg data-testid="download-icon" role="img" aria-hidden="true" class="gl-button-icon gl-icon s16 gl-fill-current"><use href="/assets/icons-ca86b3ebff8cbe14f7728864eabad153d00b66986018226fe439015884de11c2.svg#download"></use></svg>  <!----></a> <!----></div></div></div> <!----> <div class="gl-flex blob-viewer"><!----> <div data-type="simple" data-path="src/sbbs3/zmodem.c" data-testid="blob-viewer-file-content" class="file-content code js-syntax-highlight blob-content blob-viewer gl-flex gl-w-full gl-flex-col gl-overflow-auto white"><!----> <div class="gl-flex"><div class="gl-absolute gl-flex gl-flex-col"><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1" data-line-number="1" class="file-line-num gl-select-none !gl-shadow-none">
        1
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L2" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L2" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L2" data-line-number="2" class="file-line-num gl-select-none !gl-shadow-none">
        2
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L3" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L3" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L3" data-line-number="3" class="file-line-num gl-select-none !gl-shadow-none">
        3
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L4" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L4" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L4" data-line-number="4" class="file-line-num gl-select-none !gl-shadow-none">
        4
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L5" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L5" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L5" data-line-number="5" class="file-line-num gl-select-none !gl-shadow-none">
        5
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L6" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L6" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L6" data-line-number="6" class="file-line-num gl-select-none !gl-shadow-none">
        6
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L7" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L7" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L7" data-line-number="7" class="file-line-num gl-select-none !gl-shadow-none">
        7
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L8" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L8" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L8" data-line-number="8" class="file-line-num gl-select-none !gl-shadow-none">
        8
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L9" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L9" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L9" data-line-number="9" class="file-line-num gl-select-none !gl-shadow-none">
        9
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L10" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L10" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L10" data-line-number="10" class="file-line-num gl-select-none !gl-shadow-none">
        10
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L11" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L11" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L11" data-line-number="11" class="file-line-num gl-select-none !gl-shadow-none">
        11
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L12" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L12" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L12" data-line-number="12" class="file-line-num gl-select-none !gl-shadow-none">
        12
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L13" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L13" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L13" data-line-number="13" class="file-line-num gl-select-none !gl-shadow-none">
        13
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L14" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L14" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L14" data-line-number="14" class="file-line-num gl-select-none !gl-shadow-none">
        14
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L15" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L15" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L15" data-line-number="15" class="file-line-num gl-select-none !gl-shadow-none">
        15
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L16" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L16" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L16" data-line-number="16" class="file-line-num gl-select-none !gl-shadow-none">
        16
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L17" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L17" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L17" data-line-number="17" class="file-line-num gl-select-none !gl-shadow-none">
        17
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L18" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L18" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L18" data-line-number="18" class="file-line-num gl-select-none !gl-shadow-none">
        18
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L19" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L19" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L19" data-line-number="19" class="file-line-num gl-select-none !gl-shadow-none">
        19
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L20" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L20" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L20" data-line-number="20" class="file-line-num gl-select-none !gl-shadow-none">
        20
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L21" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L21" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L21" data-line-number="21" class="file-line-num gl-select-none !gl-shadow-none">
        21
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L22" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L22" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L22" data-line-number="22" class="file-line-num gl-select-none !gl-shadow-none">
        22
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L23" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L23" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L23" data-line-number="23" class="file-line-num gl-select-none !gl-shadow-none">
        23
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L24" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L24" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L24" data-line-number="24" class="file-line-num gl-select-none !gl-shadow-none">
        24
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L25" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L25" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L25" data-line-number="25" class="file-line-num gl-select-none !gl-shadow-none">
        25
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L26" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L26" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L26" data-line-number="26" class="file-line-num gl-select-none !gl-shadow-none">
        26
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L27" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L27" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L27" data-line-number="27" class="file-line-num gl-select-none !gl-shadow-none">
        27
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L28" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L28" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L28" data-line-number="28" class="file-line-num gl-select-none !gl-shadow-none">
        28
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L29" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L29" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L29" data-line-number="29" class="file-line-num gl-select-none !gl-shadow-none">
        29
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L30" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L30" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L30" data-line-number="30" class="file-line-num gl-select-none !gl-shadow-none">
        30
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L31" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L31" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L31" data-line-number="31" class="file-line-num gl-select-none !gl-shadow-none">
        31
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L32" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L32" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L32" data-line-number="32" class="file-line-num gl-select-none !gl-shadow-none">
        32
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L33" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L33" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L33" data-line-number="33" class="file-line-num gl-select-none !gl-shadow-none">
        33
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L34" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L34" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L34" data-line-number="34" class="file-line-num gl-select-none !gl-shadow-none">
        34
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L35" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L35" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L35" data-line-number="35" class="file-line-num gl-select-none !gl-shadow-none">
        35
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L36" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L36" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L36" data-line-number="36" class="file-line-num gl-select-none !gl-shadow-none">
        36
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L37" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L37" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L37" data-line-number="37" class="file-line-num gl-select-none !gl-shadow-none">
        37
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L38" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L38" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L38" data-line-number="38" class="file-line-num gl-select-none !gl-shadow-none">
        38
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L39" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L39" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L39" data-line-number="39" class="file-line-num gl-select-none !gl-shadow-none">
        39
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L40" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L40" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L40" data-line-number="40" class="file-line-num gl-select-none !gl-shadow-none">
        40
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L41" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L41" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L41" data-line-number="41" class="file-line-num gl-select-none !gl-shadow-none">
        41
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L42" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L42" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L42" data-line-number="42" class="file-line-num gl-select-none !gl-shadow-none">
        42
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L43" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L43" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L43" data-line-number="43" class="file-line-num gl-select-none !gl-shadow-none">
        43
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L44" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L44" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L44" data-line-number="44" class="file-line-num gl-select-none !gl-shadow-none">
        44
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L45" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L45" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L45" data-line-number="45" class="file-line-num gl-select-none !gl-shadow-none">
        45
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L46" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L46" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L46" data-line-number="46" class="file-line-num gl-select-none !gl-shadow-none">
        46
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L47" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L47" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L47" data-line-number="47" class="file-line-num gl-select-none !gl-shadow-none">
        47
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L48" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L48" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L48" data-line-number="48" class="file-line-num gl-select-none !gl-shadow-none">
        48
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L49" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L49" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L49" data-line-number="49" class="file-line-num gl-select-none !gl-shadow-none">
        49
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L50" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L50" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L50" data-line-number="50" class="file-line-num gl-select-none !gl-shadow-none">
        50
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L51" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L51" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L51" data-line-number="51" class="file-line-num gl-select-none !gl-shadow-none">
        51
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L52" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L52" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L52" data-line-number="52" class="file-line-num gl-select-none !gl-shadow-none">
        52
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L53" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L53" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L53" data-line-number="53" class="file-line-num gl-select-none !gl-shadow-none">
        53
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L54" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L54" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L54" data-line-number="54" class="file-line-num gl-select-none !gl-shadow-none">
        54
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L55" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L55" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L55" data-line-number="55" class="file-line-num gl-select-none !gl-shadow-none">
        55
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L56" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L56" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L56" data-line-number="56" class="file-line-num gl-select-none !gl-shadow-none">
        56
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L57" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L57" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L57" data-line-number="57" class="file-line-num gl-select-none !gl-shadow-none">
        57
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L58" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L58" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L58" data-line-number="58" class="file-line-num gl-select-none !gl-shadow-none">
        58
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L59" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L59" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L59" data-line-number="59" class="file-line-num gl-select-none !gl-shadow-none">
        59
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L60" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L60" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L60" data-line-number="60" class="file-line-num gl-select-none !gl-shadow-none">
        60
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L61" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L61" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L61" data-line-number="61" class="file-line-num gl-select-none !gl-shadow-none">
        61
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L62" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L62" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L62" data-line-number="62" class="file-line-num gl-select-none !gl-shadow-none">
        62
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L63" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L63" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L63" data-line-number="63" class="file-line-num gl-select-none !gl-shadow-none">
        63
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L64" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L64" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L64" data-line-number="64" class="file-line-num gl-select-none !gl-shadow-none">
        64
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L65" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L65" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L65" data-line-number="65" class="file-line-num gl-select-none !gl-shadow-none">
        65
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L66" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L66" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L66" data-line-number="66" class="file-line-num gl-select-none !gl-shadow-none">
        66
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L67" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L67" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L67" data-line-number="67" class="file-line-num gl-select-none !gl-shadow-none">
        67
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L68" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L68" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L68" data-line-number="68" class="file-line-num gl-select-none !gl-shadow-none">
        68
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L69" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L69" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L69" data-line-number="69" class="file-line-num gl-select-none !gl-shadow-none">
        69
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L70" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L70" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L70" data-line-number="70" class="file-line-num gl-select-none !gl-shadow-none">
        70
      </a></div></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" style="margin-left: 96px;"><div class="line" lang="c" id="LC1"><span class="hljs-comment">/* zmodem.c */</span></div>
<div class="line" lang="c" id="LC2"></div>
<div class="line" lang="c" id="LC3"><span class="hljs-comment">/* Synchronet ZMODEM Functions */</span></div>
<div class="line" lang="c" id="LC4"></div>
<div class="line" lang="c" id="LC5"><span class="hljs-comment">/******************************************************************************/</span></div>
<div class="line" lang="c" id="LC6"><span class="hljs-comment">/* Project : Unite!       File : zmodem general        Version : 1.02         */</span></div>
<div class="line" lang="c" id="LC7"><span class="hljs-comment">/*                                                                            */</span></div>
<div class="line" lang="c" id="LC8"><span class="hljs-comment"><span class="hljs-comment">/* (C)</span><span class="hljs-comment"> Mattheij Computer Service </span><span class="hljs-comment">1994                                         */</span></span></div>
<div class="line" lang="c" id="LC9"><span class="hljs-comment"><span class="hljs-comment">/*</span></span></div>
<div class="line" lang="c" id="LC10"><span class="hljs-comment"> *	Date: Thu, 19 Nov 2015 10:10:02 +0100</span></div>
<div class="line" lang="c" id="LC11"><span class="hljs-comment"> *	From: Jacques Mattheij</span></div>
<div class="line" lang="c" id="LC12"><span class="hljs-comment"> *	Subject: Re: zmodem license</span></div>
<div class="line" lang="c" id="LC13"><span class="hljs-comment"> *	To: Stephen Hurd, Fernando Toledo</span></div>
<div class="line" lang="c" id="LC14"><span class="hljs-comment"> *	CC: Rob Swindell</span></div>
<div class="line" lang="c" id="LC15"><span class="hljs-comment"> *</span></div>
<div class="line" lang="c" id="LC16"><span class="hljs-comment"> *	Hello</span><span class="hljs-comment"> there to all </span><span class="hljs-comment">of you,</span></div>
<div class="line" lang="c" id="LC17"><span class="hljs-comment"> *</span></div>
<div class="line" lang="c" id="LC18"><span class="hljs-comment"> *	So,</span><span class="hljs-comment"> this email will </span><span class="hljs-comment">then signify as the transfer of</span><span class="hljs-comment"> any and all </span><span class="hljs-comment">rights I</span></div>
<div class="line" lang="c" id="LC19"><span class="hljs-comment"> *	held up</span><span class="hljs-comment"> to this point </span><span class="hljs-comment">with</span><span class="hljs-comment"> relation to the </span><span class="hljs-comment">copyright of the zmodem</span></div>
<div class="line" lang="c" id="LC20"><span class="hljs-comment"> *	package as released by me</span><span class="hljs-comment"> many years ago </span><span class="hljs-comment">and</span><span class="hljs-comment"> all associated files </span><span class="hljs-comment">to</span></div>
<div class="line" lang="c" id="LC21"><span class="hljs-comment"> *	Stephen</span><span class="hljs-comment"> Hurd. Fernando Toledo </span><span class="hljs-comment">and</span><span class="hljs-comment"> Rob Swindell are </span><span class="hljs-comment">named as</span></div>
<div class="line" lang="c" id="LC22"><span class="hljs-comment"> *	witnesses to this transfer.</span></div>
<div class="line" lang="c" id="LC23"><span class="hljs-comment"> *</span></div>
<div class="line" lang="c" id="LC24"><span class="hljs-comment"> *	...</span></div>
<div class="line" lang="c" id="LC25"><span class="hljs-comment"> *</span></div>
<div class="line" lang="c" id="LC26"><span class="hljs-comment"> *	best regards,</span></div>
<div class="line" lang="c" id="LC27"><span class="hljs-comment"> *</span></div>
<div class="line" lang="c" id="LC28"><span class="hljs-comment"> *	Jacques Mattheij</span></div>
<div class="line" lang="c" id="LC29"><span class="hljs-comment"> ******************************************************************************/</span></div>
<div class="line" lang="c" id="LC30"></div>
<div class="line" lang="c" id="LC31"><span class="hljs-comment"><span class="hljs-comment">/*</span></span></div>
<div class="line" lang="c" id="LC32"><span class="hljs-comment"> *</span><span class="hljs-comment"> zmodem primitives and </span><span class="hljs-comment">other</span><span class="hljs-comment"> code common to </span><span class="hljs-comment">zmtx and zmrx</span></div>
<div class="line" lang="c" id="LC33"><span class="hljs-comment"> */</span></div>
<div class="line" lang="c" id="LC34"></div>
<div class="line" lang="c" id="LC35"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">include</span><span class="hljs-meta"> </span><span class="hljs-string">&lt;stdio.h&gt;</span></span></div>
<div class="line" lang="c" id="LC36"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">include</span><span class="hljs-meta"> </span><span class="hljs-string">&lt;string.h&gt;</span></span></div>
<div class="line" lang="c" id="LC37"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">include</span><span class="hljs-meta"> </span><span class="hljs-string">&lt;stdarg.h&gt;</span><span class="hljs-meta"> </span><span class="hljs-comment">/* va_list */</span></span></div>
<div class="line" lang="c" id="LC38"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">include</span><span class="hljs-meta"> </span><span class="hljs-string">&lt;sys/stat.h&gt;</span><span class="hljs-meta">   </span><span class="hljs-comment">/* struct stat */</span></span></div>
<div class="line" lang="c" id="LC39"></div>
<div class="line" lang="c" id="LC40"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">include</span><span class="hljs-meta"> </span><span class="hljs-string">"genwrap.h"</span></span></div>
<div class="line" lang="c" id="LC41"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">include</span><span class="hljs-meta"> </span><span class="hljs-string">"dirwrap.h"</span><span class="hljs-meta">    </span><span class="hljs-comment">/* getfname() */</span></span></div>
<div class="line" lang="c" id="LC42"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">include</span><span class="hljs-meta"> </span><span class="hljs-string">"filewrap.h"</span><span class="hljs-meta">   </span><span class="hljs-comment">/* filelength() */</span></span></div>
<div class="line" lang="c" id="LC43"></div>
<div class="line" lang="c" id="LC44"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">include</span><span class="hljs-meta"> </span><span class="hljs-string">"zmodem.h"</span></span></div>
<div class="line" lang="c" id="LC45"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">include</span><span class="hljs-meta"> </span><span class="hljs-string">"crc16.h"</span></span></div>
<div class="line" lang="c" id="LC46"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">include</span><span class="hljs-meta"> </span><span class="hljs-string">"crc32.h"</span></span></div>
<div class="line" lang="c" id="LC47"></div>
<div class="line" lang="c" id="LC48"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">include</span><span class="hljs-meta"> </span><span class="hljs-string">"sexyz.h"</span></span></div>
<div class="line" lang="c" id="LC49"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">include</span><span class="hljs-meta"> </span><span class="hljs-string">"telnet.h"</span></span></div>
<div class="line" lang="c" id="LC50"></div>
<div class="line" lang="c" id="LC51"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">define</span><span class="hljs-meta"> ENDOFFRAME  2</span></span></div>
<div class="line" lang="c" id="LC52"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">define</span><span class="hljs-meta"> FRAMEOK     1</span></span></div>
<div class="line" lang="c" id="LC53"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">define</span><span class="hljs-meta"> TIMEOUT         -1  </span><span class="hljs-comment"><span class="hljs-comment">/* rx</span><span class="hljs-comment"> routine did not </span><span class="hljs-comment">receive</span><span class="hljs-comment"> a character within </span><span class="hljs-comment">timeout */</span></span></span></div>
<div class="line" lang="c" id="LC54"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">define</span><span class="hljs-meta"> INVHDR          -2  </span><span class="hljs-comment"><span class="hljs-comment">/* invalid header received;</span><span class="hljs-comment"> but within timeout </span><span class="hljs-comment">*/</span></span></span></div>
<div class="line" lang="c" id="LC55"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">define</span><span class="hljs-meta"> ABORTED         -3  </span><span class="hljs-comment">/* Aborted *or* disconnected */</span></span></div>
<div class="line" lang="c" id="LC56"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">define</span><span class="hljs-meta"> SUBPKTOVERFLOW  -4  </span><span class="hljs-comment"><span class="hljs-comment">/*</span><span class="hljs-comment"> Subpacket received more </span><span class="hljs-comment">than block length */</span></span></span></div>
<div class="line" lang="c" id="LC57"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">define</span><span class="hljs-meta"> CRCFAILED       -5  </span><span class="hljs-comment">/* Failed CRC comparison */</span></span></div>
<div class="line" lang="c" id="LC58"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">define</span><span class="hljs-meta"> INVALIDSUBPKT   -6  </span><span class="hljs-comment"><span class="hljs-comment">/*</span><span class="hljs-comment"> Invalid Subpacket Type </span><span class="hljs-comment">*/</span></span></span></div>
<div class="line" lang="c" id="LC59"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">define</span><span class="hljs-meta"> ZDLEESC 0x8000  </span><span class="hljs-comment">/* one of ZCRCE; ZCRCG; ZCRCQ or ZCRCW was received; ZDLE escaped */</span></span></div>
<div class="line" lang="c" id="LC60"></div>
<div class="line" lang="c" id="LC61"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">define</span><span class="hljs-meta"> BADSUBPKT   0x80</span></span></div>
<div class="line" lang="c" id="LC62"></div>
<div class="line" lang="c" id="LC63"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">define</span><span class="hljs-meta"> SEND_SUCCESS    0</span></span></div>
<div class="line" lang="c" id="LC64"></div>
<div class="line" lang="c" id="LC65"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">define</span><span class="hljs-meta"> HDRLEN     5    </span><span class="hljs-comment"><span class="hljs-comment">/* size of</span><span class="hljs-comment"> a zmodem header </span><span class="hljs-comment">*/</span></span></span></div>
<div class="line" lang="c" id="LC66"></div>
<div class="line" lang="c" id="LC67"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">define</span><span class="hljs-meta"> SET_PARITY(c)	((c) | 0x80)</span></span></div>
<div class="line" lang="c" id="LC68"><span class="hljs-meta"><span class="hljs-meta">#</span><span class="hljs-keyword">define</span><span class="hljs-meta"> STRIPPED_PARITY(c)  ((c) &amp; 0x7f)</span></span></div>
<div class="line" lang="c" id="LC69"></div>
<div class="line" lang="c" id="LC70"><span class="hljs-type">static</span><span class=""> </span><span class="hljs-type">int</span><span class=""> </span><span class="hljs-title.function">lprintf</span><span class="hljs-params"><span class="hljs-params">(</span><span class="hljs-type">zmodem_t</span><span class="hljs-params">* zm, </span><span class="hljs-type">int</span><span class="hljs-params"> level, </span><span class="hljs-type">const</span><span class="hljs-params"> </span><span class="hljs-type">char</span><span class="hljs-params"> *fmt, ...)</span></span></div></code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">{
	va_list argptr;
	char    sbuf[1024];

	if (zm-&gt;lputs == NULL)
		return -1;
	if (zm-&gt;log_level != NULL)
		if (level &gt; *zm-&gt;log_level)
			return 0;

	va_start(argptr, fmt);
	vsnprintf(sbuf, sizeof(sbuf), fmt, argptr);
	sbuf[sizeof(sbuf) - 1] = 0;
	va_end(argptr);
	return zm-&gt;lputs(zm-&gt;cbdata, level, sbuf);
}

static BOOL is_connected(zmodem_t* zm)
{
	if (zm-&gt;is_connected != NULL)
		return zm-&gt;is_connected(zm-&gt;cbdata);
	return TRUE;
}

static BOOL is_cancelled(zmodem_t* zm)
{
	if (zm-&gt;is_cancelled != NULL)
		return zm-&gt;cancelled = zm-&gt;is_cancelled(zm-&gt;cbdata);
	return zm-&gt;cancelled;
}

static BOOL is_data_waiting(zmodem_t* zm, unsigned timeout)
{
	if (zm-&gt;data_waiting)
		return zm-&gt;data_waiting(zm-&gt;cbdata, timeout);
	return FALSE;
}

static char *chr(int ch)
{
	static char str[25];

	switch (ch) {
		case TIMEOUT:           return "TIMEOUT";
		case ABORTED:           return "ABORTED";
		case SUBPKTOVERFLOW:    return "Subpacket Overflow";
		case CRCFAILED:         return "CRC ERROR";
		case INVALIDSUBPKT:     return "Invalid Subpacket";
		case ZRQINIT:           return "ZRQINIT";
		case ZRINIT:            return "ZRINIT";
		case ZSINIT:            return "ZSINIT";
		case ZACK:              return "ZACK";
		case ZFILE:             return "ZFILE";
		case ZSKIP:             return "ZSKIP";
		case ZCRC:              return "ZCRC";
		case ZNAK:              return "ZNAK";
		case ZABORT:            return "ZABORT";
		case ZFIN:              return "ZFIN";
		case ZRPOS:             return "ZRPOS";
		case ZDATA:             return "ZDATA";
		case ZEOF:              return "ZEOF";
		case ZFERR:             return "ZFERR";
		case ZPAD:              return "ZPAD";
		case ZCAN:              return "ZCAN";
		case ZDLE:              return "ZDLE";
		case ZDLEE:             return "ZDLEE";
		case ZBIN:              return "ZBIN";
		case ZHEX:              return "ZHEX";
		case ZBIN32:            return "ZBIN32";
		case ZRESC:             return "ZRESC";</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">		case ZCRCE:             return "ZCRCE";
		case ZCRCG:             return "ZCRCG";
		case ZCRCQ:             return "ZCRCQ";
		case ZCRCW:             return "ZCRCW";
		case XON:               return "XON";
		case XOFF:              return "XOFF";
	}
	if (ch &lt; 0)
		sprintf(str, "%d", ch);
	else if (ch &gt;= ' ' &amp;&amp; ch &lt;= '~')
		sprintf(str, "'%c' (%02Xh)", (uchar)ch, (uchar)ch);
	else
		sprintf(str, "%u (%02Xh)", (uchar)ch, (uchar)ch);
	return str;
}

static char* frame_desc(int frame)
{
	static char str[25];

	if (frame == TIMEOUT)
		return "TIMEOUT";

	if (frame == INVHDR)
		return "Invalid Header";

	if (frame == ABORTED)
		return "Aborted";

	if (frame &gt;= 0 &amp;&amp; (frame &amp; BADSUBPKT)) {
		strcpy(str, "BAD ");
		switch (frame &amp; ~BADSUBPKT) {
			case ZRQINIT:       strcat(str, "ZRQINIT");      break;
			case ZRINIT:        strcat(str, "ZRINIT");       break;
			case ZSINIT:        strcat(str, "ZSINIT");       break;
			case ZACK:          strcat(str, "ZACK");         break;
			case ZFILE:         strcat(str, "ZFILE");        break;
			case ZSKIP:         strcat(str, "ZSKIP");        break;
			case ZNAK:          strcat(str, "ZNAK");         break;
			case ZABORT:        strcat(str, "ZABORT");       break;
			case ZFIN:          strcat(str, "ZFIN");         break;
			case ZRPOS:         strcat(str, "ZRPOS");        break;
			case ZDATA:         strcat(str, "ZDATA");        break;
			case ZEOF:          strcat(str, "ZEOF");         break;
			case ZFERR:         strcat(str, "ZFERR");        break;
			case ZCRC:          strcat(str, "ZCRC");         break;
			case ZCHALLENGE:    strcat(str, "ZCHALLENGE");   break;
			case ZCOMPL:        strcat(str, "ZCOMPL");       break;
			case ZCAN:          strcat(str, "ZCAN");         break;
			case ZFREECNT:      strcat(str, "ZFREECNT");     break;
			case ZCOMMAND:      strcat(str, "ZCOMMAND");     break;
			case ZSTDERR:       strcat(str, "ZSTDERR");      break;
			default:
				sprintf(str, "Unknown (%08X)", frame);
				break;
		}
	} else
		return chr(frame);
	return str;
}

ulong frame_pos(zmodem_t* zm, int type)
{
	switch (type) {
		case ZRPOS:
		case ZACK:
		case ZEOF:
		case ZDATA:
			return zm-&gt;rxd_header_pos;
	}</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">
	return 0;
}

/*
 * read bytes as long as rdchk indicates that
 * more data is available.
 */

void zmodem_recv_purge(zmodem_t* zm, unsigned timeout)
{
	int c;

	while ((c = zm-&gt;recv_byte(zm-&gt;cbdata, timeout)) &gt;= 0) {
		lprintf(zm, LOG_DEBUG, "Purging data in receive buffer: %s", chr(c));
	}
}

/*
 * Flush the output buffer
 */
void zmodem_flush(zmodem_t* zm)
{
	if (zm-&gt;flush != NULL)
		zm-&gt;flush(zm);
}

/*
 * transmit a character.
 * this is the raw modem interface
 */
/* Returns 0 on success */
int zmodem_send_raw(zmodem_t* zm, unsigned char ch)
{
	int result;

	if ((result = zm-&gt;send_byte(zm-&gt;cbdata, ch, zm-&gt;send_timeout)) != SEND_SUCCESS)
		lprintf(zm, LOG_ERR, "%s ERROR: %d", __FUNCTION__, result);
	else
		zm-&gt;last_sent = ch;

	return result;
}

/*
 * transmit a character ZDLE escaped
 */

int zmodem_send_esc(zmodem_t* zm, unsigned char c)
{
	int result;

	if ((result = zmodem_send_raw(zm, ZDLE)) != SEND_SUCCESS) {
		lprintf(zm, LOG_ERR, "%s ERROR: %d", __FUNCTION__, result);
		return result;
	}
	/*
	 * exclusive or; not an or so ZDLE becomes ZDLEE
	 */
	return zmodem_send_raw(zm, (uchar)(c ^ 0x40));
}

/*
 * transmit a character; ZDLE escaping if appropriate
 */

int zmodem_tx(zmodem_t* zm, unsigned char c)
{
	int result;
</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">	switch (c) {
		case DLE:
		case DLE | 0x80:          /* even if high-bit set */
		case XON:
		case XON | 0x80:
		case XOFF:
		case XOFF | 0x80:
		case ZDLE:
			return zmodem_send_esc(zm, c);
		case CR:
		case CR | 0x80:
			if (zm-&gt;escape_ctrl_chars &amp;&amp; (zm-&gt;last_sent &amp; 0x7f) == '@')
				return zmodem_send_esc(zm, c);
			break;
		case TELNET_IAC:
			if (zm-&gt;escape_telnet_iac) {
				if ((result = zmodem_send_raw(zm, ZDLE)) != SEND_SUCCESS)
					return result;
				return zmodem_send_raw(zm, ZRUB1);
			}
			break;
		default:
			if (zm-&gt;escape_ctrl_chars &amp;&amp; (c &amp; 0x60) == 0)
				return zmodem_send_esc(zm, c);
			break;
	}
	/*
	 * anything that ends here is so normal we might as well transmit it.
	 */
	return zmodem_send_raw(zm, c);
}

/**********************************************/
/* Output single byte as two hex ASCII digits */
/**********************************************/
int zmodem_send_hex(zmodem_t* zm, uchar val)
{
	char* xdigit = "0123456789abcdef";
	int   result;

//	lprintf(zm, LOG_DEBUG, __FUNCTION__ " %02X",val);

	if ((result = zmodem_send_raw(zm, xdigit[val &gt;&gt; 4])) != SEND_SUCCESS)
		return result;
	return zmodem_send_raw(zm, xdigit[val &amp; 0xf]);
}

int zmodem_send_padded_zdle(zmodem_t* zm)
{
	int result;

	if ((result = zmodem_send_raw(zm, ZPAD)) != SEND_SUCCESS)
		return result;
	if ((result = zmodem_send_raw(zm, ZPAD)) != SEND_SUCCESS)
		return result;
	return zmodem_send_raw(zm, ZDLE);
}

/*
 * transmit a hex header.
 * these routines use tx_raw because we're sure that all the
 * characters are not to be escaped.
 */
int zmodem_send_hex_header(zmodem_t* zm, unsigned char * p)
{
	int                i;
	int                result;
	uchar              type = *p;
	unsigned short int crc;
</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">//	lprintf(zm, LOG_DEBUG, __FUNCTION__ " %s", chr(type));

	if ((result = zmodem_send_padded_zdle(zm)) != SEND_SUCCESS)
		return result;

	if ((result = zmodem_send_raw(zm, ZHEX)) != SEND_SUCCESS)
		return result;

	/*
	 * initialise the crc
	 */

	crc = 0;

	/*
	 * transmit the header
	 */

	for (i = 0; i &lt; HDRLEN; i++) {
		if ((result = zmodem_send_hex(zm, *p)) != SEND_SUCCESS)
			return result;
		crc = ucrc16(*p, crc);
		p++;
	}

	/*
	 * update the crc as though it were zero
	 */

	/*
	 * transmit the crc
	 */

	if ((result = zmodem_send_hex(zm, (uchar)(crc &gt;&gt; 8))) != SEND_SUCCESS)
		return result;
	if ((result = zmodem_send_hex(zm, (uchar)(crc &amp; 0xff))) != SEND_SUCCESS)
		return result;

	/*
	 * end of line sequence
	 */

	if ((result = zmodem_send_raw(zm, '\r')) != SEND_SUCCESS)
		return result;
	if ((result = zmodem_send_raw(zm, '\n')) != SEND_SUCCESS)  /* FDSZ sends 0x8a instead of 0x0a */
		return result;

	if (type != ZACK &amp;&amp; type != ZFIN)
		result = zmodem_send_raw(zm, XON);

	zmodem_flush(zm);

	return result;
}

/*
 * Send ZMODEM binary header hdr
 */

int zmodem_send_bin32_header(zmodem_t* zm, unsigned char * p)
{
	int      i;
	int      result;
	uint32_t crc;

//	lprintf(zm, LOG_DEBUG, __FUNCTION__ " %s", chr(*p));

	if ((result = zmodem_send_padded_zdle(zm)) != SEND_SUCCESS)
		return result;
</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">	if ((result = zmodem_send_raw(zm, ZBIN32)) != SEND_SUCCESS)
		return result;

	crc = 0xffffffffL;

	for (i = 0; i &lt; HDRLEN; i++) {
		crc = ucrc32(*p, crc);
		if ((result = zmodem_tx(zm, *p++)) != SEND_SUCCESS)
			return result;
	}

	crc = ~crc;

	if ((result = zmodem_tx(zm, (uchar)((crc) &amp; 0xff))) != SEND_SUCCESS)
		return result;
	if ((result = zmodem_tx(zm, (uchar)((crc &gt;&gt;  8) &amp; 0xff))) != SEND_SUCCESS)
		return result;
	if ((result = zmodem_tx(zm, (uchar)((crc &gt;&gt; 16) &amp; 0xff))) != SEND_SUCCESS)
		return result;
	return zmodem_tx(zm, (uchar)((crc &gt;&gt; 24) &amp; 0xff));
}

int zmodem_send_bin16_header(zmodem_t* zm, unsigned char * p)
{
	int          i;
	int          result;
	unsigned int crc;

//	lprintf(zm, LOG_DEBUG, __FUNCTION__ " %s", chr(*p));

	if ((result = zmodem_send_padded_zdle(zm)) != SEND_SUCCESS)
		return result;

	if ((result = zmodem_send_raw(zm, ZBIN)) != SEND_SUCCESS)
		return result;

	crc = 0;

	for (i = 0; i &lt; HDRLEN; i++) {
		crc = ucrc16(*p, crc);
		if ((result = zmodem_tx(zm, *p++)) != SEND_SUCCESS)
			return result;
	}

	if ((result = zmodem_tx(zm, (uchar)(crc &gt;&gt; 8))) != SEND_SUCCESS)
		return result;
	return zmodem_tx(zm, (uchar)(crc &amp; 0xff));
}


/*
 * transmit a header using either hex 16 bit crc or binary 32 bit crc
 * depending on the receivers capabilities
 * we dont bother with variable length headers. I dont really see their
 * advantage and they would clutter the code unneccesarily
 */

int zmodem_send_bin_header(zmodem_t* zm, unsigned char * p)
{
	if (zm-&gt;can_fcs_32 &amp;&amp; !zm-&gt;want_fcs_16)
		return zmodem_send_bin32_header(zm, p);
	return zmodem_send_bin16_header(zm, p);
}

/*
 * data subpacket transmission
 */

int zmodem_send_data32(zmodem_t* zm, uchar subpkt_type, unsigned char * p, size_t l)
{</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">	int      result;
	uint32_t crc;

//	lprintf(zm, LOG_DEBUG, __FUNCTION__ " %s (%u bytes)", chr(subpkt_type), l);

	crc = 0xffffffffl;

	while (l &gt; 0) {
		crc = ucrc32(*p, crc);
		if ((result = zmodem_tx(zm, *p++)) != SEND_SUCCESS)
			return result;
		l--;
	}

	crc = ucrc32(subpkt_type, crc);

	if ((result = zmodem_send_raw(zm, ZDLE)) != SEND_SUCCESS)
		return result;
	if ((result = zmodem_send_raw(zm, subpkt_type)) != SEND_SUCCESS)
		return result;

	crc = ~crc;

	if ((result = zmodem_tx(zm, (uchar) ((crc) &amp; 0xff))) != SEND_SUCCESS)
		return result;
	if ((result = zmodem_tx(zm, (uchar) ((crc &gt;&gt; 8) &amp; 0xff))) != SEND_SUCCESS)
		return result;
	if ((result = zmodem_tx(zm, (uchar) ((crc &gt;&gt; 16) &amp; 0xff))) != SEND_SUCCESS)
		return result;
	return zmodem_tx(zm, (uchar) ((crc &gt;&gt; 24) &amp; 0xff));
}

int zmodem_send_data16(zmodem_t* zm, uchar subpkt_type, unsigned char * p, size_t l)
{
	int            result;
	unsigned short crc;

//	lprintf(zm, LOG_DEBUG, __FUNCTION__ " %s (%u bytes)", chr(subpkt_type), l);

	crc = 0;

	while (l &gt; 0) {
		crc = ucrc16(*p, crc);
		if ((result = zmodem_tx(zm, *p++)) != SEND_SUCCESS)
			return result;
		l--;
	}

	crc = ucrc16(subpkt_type, crc);

	if ((result = zmodem_send_raw(zm, ZDLE)) != SEND_SUCCESS)
		return result;
	if ((result = zmodem_send_raw(zm, subpkt_type)) != SEND_SUCCESS)
		return result;

	if ((result = zmodem_tx(zm, (uchar)(crc &gt;&gt; 8))) != SEND_SUCCESS)
		return result;
	return zmodem_tx(zm, (uchar)(crc &amp; 0xff));
}

BOOL zmodem_end_of_frame(int subpkt_type)
{
	return subpkt_type == ZCRCW || subpkt_type == ZCRCE;
}

/*
 * send a data subpacket using crc 16 or crc 32 as desired by the receiver
 */

int zmodem_send_data_subpkt(zmodem_t* zm, uchar subpkt_type, unsigned char* data, size_t len)</code></pre></div></div><div class="gl-flex"><div class="gl-absolute gl-flex gl-flex-col"><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L561" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L561" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L561" data-line-number="561" class="file-line-num gl-select-none !gl-shadow-none">
        561
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L562" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L562" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L562" data-line-number="562" class="file-line-num gl-select-none !gl-shadow-none">
        562
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L563" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L563" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L563" data-line-number="563" class="file-line-num gl-select-none !gl-shadow-none">
        563
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L564" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L564" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L564" data-line-number="564" class="file-line-num gl-select-none !gl-shadow-none">
        564
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L565" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L565" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L565" data-line-number="565" class="file-line-num gl-select-none !gl-shadow-none">
        565
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L566" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L566" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L566" data-line-number="566" class="file-line-num gl-select-none !gl-shadow-none">
        566
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L567" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L567" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L567" data-line-number="567" class="file-line-num gl-select-none !gl-shadow-none">
        567
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L568" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L568" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L568" data-line-number="568" class="file-line-num gl-select-none !gl-shadow-none">
        568
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L569" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L569" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L569" data-line-number="569" class="file-line-num gl-select-none !gl-shadow-none">
        569
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L570" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L570" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L570" data-line-number="570" class="file-line-num gl-select-none !gl-shadow-none">
        570
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L571" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L571" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L571" data-line-number="571" class="file-line-num gl-select-none !gl-shadow-none">
        571
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L572" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L572" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L572" data-line-number="572" class="file-line-num gl-select-none !gl-shadow-none">
        572
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L573" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L573" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L573" data-line-number="573" class="file-line-num gl-select-none !gl-shadow-none">
        573
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L574" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L574" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L574" data-line-number="574" class="file-line-num gl-select-none !gl-shadow-none">
        574
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L575" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L575" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L575" data-line-number="575" class="file-line-num gl-select-none !gl-shadow-none">
        575
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L576" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L576" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L576" data-line-number="576" class="file-line-num gl-select-none !gl-shadow-none">
        576
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L577" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L577" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L577" data-line-number="577" class="file-line-num gl-select-none !gl-shadow-none">
        577
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L578" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L578" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L578" data-line-number="578" class="file-line-num gl-select-none !gl-shadow-none">
        578
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L579" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L579" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L579" data-line-number="579" class="file-line-num gl-select-none !gl-shadow-none">
        579
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L580" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L580" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L580" data-line-number="580" class="file-line-num gl-select-none !gl-shadow-none">
        580
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L581" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L581" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L581" data-line-number="581" class="file-line-num gl-select-none !gl-shadow-none">
        581
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L582" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L582" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L582" data-line-number="582" class="file-line-num gl-select-none !gl-shadow-none">
        582
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L583" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L583" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L583" data-line-number="583" class="file-line-num gl-select-none !gl-shadow-none">
        583
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L584" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L584" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L584" data-line-number="584" class="file-line-num gl-select-none !gl-shadow-none">
        584
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L585" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L585" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L585" data-line-number="585" class="file-line-num gl-select-none !gl-shadow-none">
        585
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L586" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L586" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L586" data-line-number="586" class="file-line-num gl-select-none !gl-shadow-none">
        586
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L587" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L587" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L587" data-line-number="587" class="file-line-num gl-select-none !gl-shadow-none">
        587
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L588" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L588" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L588" data-line-number="588" class="file-line-num gl-select-none !gl-shadow-none">
        588
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L589" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L589" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L589" data-line-number="589" class="file-line-num gl-select-none !gl-shadow-none">
        589
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L590" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L590" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L590" data-line-number="590" class="file-line-num gl-select-none !gl-shadow-none">
        590
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L591" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L591" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L591" data-line-number="591" class="file-line-num gl-select-none !gl-shadow-none">
        591
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L592" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L592" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L592" data-line-number="592" class="file-line-num gl-select-none !gl-shadow-none">
        592
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L593" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L593" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L593" data-line-number="593" class="file-line-num gl-select-none !gl-shadow-none">
        593
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L594" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L594" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L594" data-line-number="594" class="file-line-num gl-select-none !gl-shadow-none">
        594
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L595" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L595" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L595" data-line-number="595" class="file-line-num gl-select-none !gl-shadow-none">
        595
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L596" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L596" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L596" data-line-number="596" class="file-line-num gl-select-none !gl-shadow-none">
        596
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L597" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L597" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L597" data-line-number="597" class="file-line-num gl-select-none !gl-shadow-none">
        597
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L598" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L598" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L598" data-line-number="598" class="file-line-num gl-select-none !gl-shadow-none">
        598
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L599" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L599" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L599" data-line-number="599" class="file-line-num gl-select-none !gl-shadow-none">
        599
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L600" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L600" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L600" data-line-number="600" class="file-line-num gl-select-none !gl-shadow-none">
        600
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L601" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L601" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L601" data-line-number="601" class="file-line-num gl-select-none !gl-shadow-none">
        601
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L602" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L602" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L602" data-line-number="602" class="file-line-num gl-select-none !gl-shadow-none">
        602
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L603" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L603" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L603" data-line-number="603" class="file-line-num gl-select-none !gl-shadow-none">
        603
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L604" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L604" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L604" data-line-number="604" class="file-line-num gl-select-none !gl-shadow-none">
        604
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L605" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L605" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L605" data-line-number="605" class="file-line-num gl-select-none !gl-shadow-none">
        605
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L606" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L606" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L606" data-line-number="606" class="file-line-num gl-select-none !gl-shadow-none">
        606
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L607" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L607" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L607" data-line-number="607" class="file-line-num gl-select-none !gl-shadow-none">
        607
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L608" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L608" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L608" data-line-number="608" class="file-line-num gl-select-none !gl-shadow-none">
        608
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L609" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L609" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L609" data-line-number="609" class="file-line-num gl-select-none !gl-shadow-none">
        609
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L610" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L610" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L610" data-line-number="610" class="file-line-num gl-select-none !gl-shadow-none">
        610
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L611" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L611" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L611" data-line-number="611" class="file-line-num gl-select-none !gl-shadow-none">
        611
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L612" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L612" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L612" data-line-number="612" class="file-line-num gl-select-none !gl-shadow-none">
        612
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L613" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L613" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L613" data-line-number="613" class="file-line-num gl-select-none !gl-shadow-none">
        613
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L614" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L614" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L614" data-line-number="614" class="file-line-num gl-select-none !gl-shadow-none">
        614
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L615" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L615" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L615" data-line-number="615" class="file-line-num gl-select-none !gl-shadow-none">
        615
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L616" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L616" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L616" data-line-number="616" class="file-line-num gl-select-none !gl-shadow-none">
        616
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L617" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L617" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L617" data-line-number="617" class="file-line-num gl-select-none !gl-shadow-none">
        617
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L618" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L618" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L618" data-line-number="618" class="file-line-num gl-select-none !gl-shadow-none">
        618
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L619" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L619" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L619" data-line-number="619" class="file-line-num gl-select-none !gl-shadow-none">
        619
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L620" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L620" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L620" data-line-number="620" class="file-line-num gl-select-none !gl-shadow-none">
        620
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L621" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L621" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L621" data-line-number="621" class="file-line-num gl-select-none !gl-shadow-none">
        621
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L622" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L622" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L622" data-line-number="622" class="file-line-num gl-select-none !gl-shadow-none">
        622
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L623" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L623" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L623" data-line-number="623" class="file-line-num gl-select-none !gl-shadow-none">
        623
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L624" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L624" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L624" data-line-number="624" class="file-line-num gl-select-none !gl-shadow-none">
        624
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L625" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L625" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L625" data-line-number="625" class="file-line-num gl-select-none !gl-shadow-none">
        625
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L626" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L626" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L626" data-line-number="626" class="file-line-num gl-select-none !gl-shadow-none">
        626
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L627" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L627" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L627" data-line-number="627" class="file-line-num gl-select-none !gl-shadow-none">
        627
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L628" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L628" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L628" data-line-number="628" class="file-line-num gl-select-none !gl-shadow-none">
        628
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L629" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L629" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L629" data-line-number="629" class="file-line-num gl-select-none !gl-shadow-none">
        629
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L630" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L630" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L630" data-line-number="630" class="file-line-num gl-select-none !gl-shadow-none">
        630
      </a></div></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" style="margin-left: 96px;"><div class="line" lang="c" id="LC561"><span class="">{</span></div>
<div class="line" lang="c" id="LC562"><span class="">	</span><span class="hljs-type">int</span><span class=""> result;</span></div>
<div class="line" lang="c" id="LC563"></div>
<div class="line" lang="c" id="LC564"><span class="">	</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(zmodem_end_of_frame</span><span class="">(subpkt_type)</span><span class="">)</span></div>
<div class="line" lang="c" id="LC565"><span class="">		zm-&gt;frame_in_transit </span><span class="">= FALSE;</span></div>
<div class="line" lang="c" id="LC566"><span class="">	</span><span class="hljs-keyword">else</span><span class="">    </span><span class="hljs-comment">/* other subpacket (mid-frame) */</span></div>
<div class="line" lang="c" id="LC567"><span class="">		zm-&gt;frame_in_transit = TRUE;</span></div>
<div class="line" lang="c" id="LC568"></div>
<div class="line" lang="c" id="LC569"><span class="">	</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(!zm-&gt;want_fcs_16 &amp;&amp; zm-&gt;can_fcs_32)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC570"><span class="">		</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(</span><span class="">(result = zmodem_send_data32</span><span class="">(zm, subpkt_type, data, len)</span><span class="">)</span><span class=""> != SEND_SUCCESS)</span></div>
<div class="line" lang="c" id="LC571"><span class="">			</span><span class="hljs-keyword">return</span><span class=""> result;</span></div>
<div class="line" lang="c" id="LC572"><span class="">	}</span></div>
<div class="line" lang="c" id="LC573"><span class="">	</span><span class="hljs-keyword">else</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC574"><span class="">		</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(</span><span class="">(result = zmodem_send_data16</span><span class="">(zm, subpkt_type, data, len)</span><span class="">)</span><span class=""> != SEND_SUCCESS)</span></div>
<div class="line" lang="c" id="LC575"><span class="">			</span><span class="hljs-keyword">return</span><span class=""> result;</span></div>
<div class="line" lang="c" id="LC576"><span class="">	}</span></div>
<div class="line" lang="c" id="LC577"></div>
<div class="line" lang="c" id="LC578"><span class="">	</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(subpkt_type == ZCRCW)</span></div>
<div class="line" lang="c" id="LC579"><span class="">		result </span><span class="">= zmodem_send_raw</span><span class="">(zm, XON)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC580"></div>
<div class="line" lang="c" id="LC581"><span class="">	zmodem_flush</span><span class="">(zm)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC582"></div>
<div class="line" lang="c" id="LC583"><span class="">	</span><span class="hljs-keyword">return</span><span class=""> result;</span></div>
<div class="line" lang="c" id="LC584"><span class="">}</span></div>
<div class="line" lang="c" id="LC585"></div>
<div class="line" lang="c" id="LC586"><span class="hljs-type">int</span><span class=""> </span><span class="hljs-title.function">zmodem_send_data</span><span class="hljs-params"><span class="hljs-params">(</span><span class="hljs-type">zmodem_t</span><span class="hljs-params">* zm, uchar subpkt_type, </span><span class="hljs-type">unsigned</span><span class="hljs-params"> </span><span class="hljs-type">char</span><span class="hljs-params">* data, </span><span class="hljs-type">size_t</span><span class="hljs-params"> len)</span></span></div>
<div class="line" lang="c" id="LC587"><span class="">{</span></div>
<div class="line" lang="c" id="LC588"><span class="">	</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(!zm-&gt;frame_in_transit)</span><span class="">   { </span><span class="hljs-comment">/* Start of frame, include ZDATA header */</span></div>
<div class="line" lang="c" id="LC589"><span class="">		lprintf</span><span class="">(zm, LOG_DEBUG, </span><span class="hljs-string">"%lu %s Start of frame: %s"</span></div>
<div class="line" lang="c" id="LC590"><span class="">		        , </span><span class="">(ulong)</span><span class="">zm-&gt;current_file_pos, __FUNCTION__, chr</span><span class="">(subpkt_type)</span><span class="">)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC591"><span class="">		zmodem_send_pos_header</span><span class="">(zm, ZDATA, </span><span class="">(</span><span class="hljs-type">uint32_t</span><span class="">)</span><span class="">zm-&gt;current_file_pos, </span><span class="hljs-comment">/* Hex? */</span><span class=""> FALSE)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC592"><span class="">	}</span></div>
<div class="line" lang="c" id="LC593"></div>
<div class="line" lang="c" id="LC594"><span class="">	</span><span class="hljs-keyword">return</span><span class=""> zmodem_send_data_subpkt</span><span class="">(zm, subpkt_type, data, len)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC595"><span class="">}</span></div>
<div class="line" lang="c" id="LC596"></div>
<div class="line" lang="c" id="LC597"><span class="hljs-type">int</span><span class=""> </span><span class="hljs-title.function">zmodem_send_pos_header</span><span class="hljs-params"><span class="hljs-params">(</span><span class="hljs-type">zmodem_t</span><span class="hljs-params">* zm, </span><span class="hljs-type">int</span><span class="hljs-params"> type, </span><span class="hljs-type">int32_t</span><span class="hljs-params"> pos, BOOL hex)</span></span></div>
<div class="line" lang="c" id="LC598"><span class="">{</span></div>
<div class="line" lang="c" id="LC599"><span class="">	uchar header[</span><span class="hljs-number">5</span><span class="">];</span></div>
<div class="line" lang="c" id="LC600"></div>
<div class="line" lang="c" id="LC601"><span class="">	lprintf</span><span class="">(zm, LOG_DEBUG, </span><span class="hljs-string">"%lu %s %s"</span><span class="">, </span><span class="">(ulong)</span><span class="">pos, __FUNCTION__, chr</span><span class="">(type)</span><span class="">)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC602"><span class="">	header[</span><span class="hljs-number">0</span><span class="">]   </span><span class="">= type;</span></div>
<div class="line" lang="c" id="LC603"><span class="">	header[ZP0] </span><span class="">= </span><span class="">(uchar)</span><span class=""> </span><span class="">(pos        &amp; </span><span class="hljs-number">0xff</span><span class="">)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC604"><span class="">	header[ZP1] </span><span class="">= </span><span class="">(uchar)</span><span class="">(</span><span class="">(pos &gt;&gt;  </span><span class="hljs-number">8</span><span class="">)</span><span class=""> &amp; </span><span class="hljs-number">0xff</span><span class="">)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC605"><span class="">	header[ZP2] </span><span class="">= </span><span class="">(uchar)</span><span class="">(</span><span class="">(pos &gt;&gt; </span><span class="hljs-number">16</span><span class="">)</span><span class=""> &amp; </span><span class="hljs-number">0xff</span><span class="">)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC606"><span class="">	header[ZP3] </span><span class="">= </span><span class="">(uchar)</span><span class="">(</span><span class="">(pos &gt;&gt; </span><span class="hljs-number">24</span><span class="">)</span><span class=""> &amp; </span><span class="hljs-number">0xff</span><span class="">)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC607"></div>
<div class="line" lang="c" id="LC608"><span class="">	</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(hex)</span></div>
<div class="line" lang="c" id="LC609"><span class="">		</span><span class="hljs-keyword">return</span><span class=""> zmodem_send_hex_header</span><span class="">(zm, header)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC610"><span class="">	</span><span class="hljs-keyword">else</span></div>
<div class="line" lang="c" id="LC611"><span class="">		</span><span class="hljs-keyword">return</span><span class=""> zmodem_send_bin_header</span><span class="">(zm, header)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC612"><span class="">}</span></div>
<div class="line" lang="c" id="LC613"></div>
<div class="line" lang="c" id="LC614"><span class="hljs-type">int</span><span class=""> </span><span class="hljs-title.function">zmodem_send_ack</span><span class="hljs-params"><span class="hljs-params">(</span><span class="hljs-type">zmodem_t</span><span class="hljs-params">* zm, </span><span class="hljs-type">int32_t</span><span class="hljs-params"> pos)</span></span></div>
<div class="line" lang="c" id="LC615"><span class="">{</span></div>
<div class="line" lang="c" id="LC616"><span class="">	</span><span class="hljs-keyword">return</span><span class=""> zmodem_send_pos_header</span><span class="">(zm, ZACK, pos, </span><span class="hljs-comment">/* Hex? */</span><span class=""> TRUE)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC617"><span class="">}</span></div>
<div class="line" lang="c" id="LC618"></div>
<div class="line" lang="c" id="LC619"><span class="hljs-type">int</span><span class=""> </span><span class="hljs-title.function">zmodem_send_zfin</span><span class="hljs-params"><span class="hljs-params">(</span><span class="hljs-type">zmodem_t</span><span class="hljs-params">* zm)</span></span></div>
<div class="line" lang="c" id="LC620"><span class="">{</span></div>
<div class="line" lang="c" id="LC621"><span class="">	</span><span class="hljs-type">unsigned</span><span class=""> </span><span class="hljs-type">char</span><span class=""> zfin_header[] </span><span class="">= { ZFIN, </span><span class="hljs-number">0</span><span class="">, </span><span class="hljs-number">0</span><span class="">, </span><span class="hljs-number">0</span><span class="">, </span><span class="hljs-number">0</span><span class=""> };</span></div>
<div class="line" lang="c" id="LC622"></div>
<div class="line" lang="c" id="LC623"><span class="">	lprintf</span><span class="">(zm, LOG_NOTICE, </span><span class="hljs-string">"%lu Finishing Session (Sending ZFIN)"</span><span class="">, </span><span class="">(ulong)</span><span class="">zm-&gt;current_file_pos)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC624"><span class="">	</span><span class="hljs-keyword">return</span><span class=""> zmodem_send_hex_header</span><span class="">(zm, zfin_header)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC625"><span class="">}</span></div>
<div class="line" lang="c" id="LC626"></div>
<div class="line" lang="c" id="LC627"><span class="hljs-type">int</span><span class=""> </span><span class="hljs-title.function">zmodem_send_zabort</span><span class="hljs-params"><span class="hljs-params">(</span><span class="hljs-type">zmodem_t</span><span class="hljs-params">* zm)</span></span></div>
<div class="line" lang="c" id="LC628"><span class="">{</span></div>
<div class="line" lang="c" id="LC629"><span class="">	lprintf</span><span class="">(zm, LOG_WARNING, </span><span class="hljs-string">"%lu Aborting Transfer (Sending ZABORT)"</span><span class="">, </span><span class="">(ulong)</span><span class="">zm-&gt;current_file_pos)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC630"><span class="">	</span><span class="hljs-keyword">return</span><span class=""> zmodem_send_pos_header</span><span class="">(zm, ZABORT, </span><span class="hljs-number">0</span><span class="">, </span><span class="hljs-comment">/* Hex? */</span><span class=""> TRUE)</span><span class="">;</span></div></code></pre></div></div><div class="gl-flex"><div class="gl-absolute gl-flex gl-flex-col"><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L631" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L631" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L631" data-line-number="631" class="file-line-num gl-select-none !gl-shadow-none">
        631
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L632" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L632" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L632" data-line-number="632" class="file-line-num gl-select-none !gl-shadow-none">
        632
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L633" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L633" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L633" data-line-number="633" class="file-line-num gl-select-none !gl-shadow-none">
        633
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L634" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L634" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L634" data-line-number="634" class="file-line-num gl-select-none !gl-shadow-none">
        634
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L635" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L635" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L635" data-line-number="635" class="file-line-num gl-select-none !gl-shadow-none">
        635
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L636" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L636" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L636" data-line-number="636" class="file-line-num gl-select-none !gl-shadow-none">
        636
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L637" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L637" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L637" data-line-number="637" class="file-line-num gl-select-none !gl-shadow-none">
        637
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L638" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L638" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L638" data-line-number="638" class="file-line-num gl-select-none !gl-shadow-none">
        638
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L639" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L639" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L639" data-line-number="639" class="file-line-num gl-select-none !gl-shadow-none">
        639
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L640" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L640" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L640" data-line-number="640" class="file-line-num gl-select-none !gl-shadow-none">
        640
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L641" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L641" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L641" data-line-number="641" class="file-line-num gl-select-none !gl-shadow-none">
        641
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L642" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L642" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L642" data-line-number="642" class="file-line-num gl-select-none !gl-shadow-none">
        642
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L643" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L643" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L643" data-line-number="643" class="file-line-num gl-select-none !gl-shadow-none">
        643
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L644" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L644" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L644" data-line-number="644" class="file-line-num gl-select-none !gl-shadow-none">
        644
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L645" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L645" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L645" data-line-number="645" class="file-line-num gl-select-none !gl-shadow-none">
        645
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L646" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L646" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L646" data-line-number="646" class="file-line-num gl-select-none !gl-shadow-none">
        646
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L647" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L647" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L647" data-line-number="647" class="file-line-num gl-select-none !gl-shadow-none">
        647
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L648" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L648" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L648" data-line-number="648" class="file-line-num gl-select-none !gl-shadow-none">
        648
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L649" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L649" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L649" data-line-number="649" class="file-line-num gl-select-none !gl-shadow-none">
        649
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L650" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L650" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L650" data-line-number="650" class="file-line-num gl-select-none !gl-shadow-none">
        650
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L651" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L651" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L651" data-line-number="651" class="file-line-num gl-select-none !gl-shadow-none">
        651
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L652" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L652" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L652" data-line-number="652" class="file-line-num gl-select-none !gl-shadow-none">
        652
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L653" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L653" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L653" data-line-number="653" class="file-line-num gl-select-none !gl-shadow-none">
        653
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L654" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L654" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L654" data-line-number="654" class="file-line-num gl-select-none !gl-shadow-none">
        654
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L655" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L655" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L655" data-line-number="655" class="file-line-num gl-select-none !gl-shadow-none">
        655
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L656" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L656" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L656" data-line-number="656" class="file-line-num gl-select-none !gl-shadow-none">
        656
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L657" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L657" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L657" data-line-number="657" class="file-line-num gl-select-none !gl-shadow-none">
        657
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L658" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L658" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L658" data-line-number="658" class="file-line-num gl-select-none !gl-shadow-none">
        658
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L659" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L659" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L659" data-line-number="659" class="file-line-num gl-select-none !gl-shadow-none">
        659
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L660" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L660" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L660" data-line-number="660" class="file-line-num gl-select-none !gl-shadow-none">
        660
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L661" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L661" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L661" data-line-number="661" class="file-line-num gl-select-none !gl-shadow-none">
        661
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L662" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L662" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L662" data-line-number="662" class="file-line-num gl-select-none !gl-shadow-none">
        662
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L663" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L663" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L663" data-line-number="663" class="file-line-num gl-select-none !gl-shadow-none">
        663
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L664" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L664" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L664" data-line-number="664" class="file-line-num gl-select-none !gl-shadow-none">
        664
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L665" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L665" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L665" data-line-number="665" class="file-line-num gl-select-none !gl-shadow-none">
        665
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L666" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L666" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L666" data-line-number="666" class="file-line-num gl-select-none !gl-shadow-none">
        666
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L667" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L667" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L667" data-line-number="667" class="file-line-num gl-select-none !gl-shadow-none">
        667
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L668" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L668" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L668" data-line-number="668" class="file-line-num gl-select-none !gl-shadow-none">
        668
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L669" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L669" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L669" data-line-number="669" class="file-line-num gl-select-none !gl-shadow-none">
        669
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L670" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L670" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L670" data-line-number="670" class="file-line-num gl-select-none !gl-shadow-none">
        670
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L671" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L671" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L671" data-line-number="671" class="file-line-num gl-select-none !gl-shadow-none">
        671
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L672" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L672" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L672" data-line-number="672" class="file-line-num gl-select-none !gl-shadow-none">
        672
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L673" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L673" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L673" data-line-number="673" class="file-line-num gl-select-none !gl-shadow-none">
        673
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L674" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L674" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L674" data-line-number="674" class="file-line-num gl-select-none !gl-shadow-none">
        674
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L675" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L675" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L675" data-line-number="675" class="file-line-num gl-select-none !gl-shadow-none">
        675
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L676" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L676" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L676" data-line-number="676" class="file-line-num gl-select-none !gl-shadow-none">
        676
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L677" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L677" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L677" data-line-number="677" class="file-line-num gl-select-none !gl-shadow-none">
        677
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L678" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L678" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L678" data-line-number="678" class="file-line-num gl-select-none !gl-shadow-none">
        678
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L679" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L679" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L679" data-line-number="679" class="file-line-num gl-select-none !gl-shadow-none">
        679
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L680" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L680" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L680" data-line-number="680" class="file-line-num gl-select-none !gl-shadow-none">
        680
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L681" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L681" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L681" data-line-number="681" class="file-line-num gl-select-none !gl-shadow-none">
        681
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L682" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L682" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L682" data-line-number="682" class="file-line-num gl-select-none !gl-shadow-none">
        682
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L683" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L683" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L683" data-line-number="683" class="file-line-num gl-select-none !gl-shadow-none">
        683
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L684" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L684" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L684" data-line-number="684" class="file-line-num gl-select-none !gl-shadow-none">
        684
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L685" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L685" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L685" data-line-number="685" class="file-line-num gl-select-none !gl-shadow-none">
        685
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L686" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L686" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L686" data-line-number="686" class="file-line-num gl-select-none !gl-shadow-none">
        686
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L687" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L687" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L687" data-line-number="687" class="file-line-num gl-select-none !gl-shadow-none">
        687
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L688" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L688" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L688" data-line-number="688" class="file-line-num gl-select-none !gl-shadow-none">
        688
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L689" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L689" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L689" data-line-number="689" class="file-line-num gl-select-none !gl-shadow-none">
        689
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L690" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L690" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L690" data-line-number="690" class="file-line-num gl-select-none !gl-shadow-none">
        690
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L691" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L691" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L691" data-line-number="691" class="file-line-num gl-select-none !gl-shadow-none">
        691
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L692" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L692" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L692" data-line-number="692" class="file-line-num gl-select-none !gl-shadow-none">
        692
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L693" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L693" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L693" data-line-number="693" class="file-line-num gl-select-none !gl-shadow-none">
        693
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L694" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L694" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L694" data-line-number="694" class="file-line-num gl-select-none !gl-shadow-none">
        694
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L695" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L695" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L695" data-line-number="695" class="file-line-num gl-select-none !gl-shadow-none">
        695
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L696" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L696" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L696" data-line-number="696" class="file-line-num gl-select-none !gl-shadow-none">
        696
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L697" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L697" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L697" data-line-number="697" class="file-line-num gl-select-none !gl-shadow-none">
        697
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L698" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L698" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L698" data-line-number="698" class="file-line-num gl-select-none !gl-shadow-none">
        698
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L699" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L699" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L699" data-line-number="699" class="file-line-num gl-select-none !gl-shadow-none">
        699
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L700" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L700" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L700" data-line-number="700" class="file-line-num gl-select-none !gl-shadow-none">
        700
      </a></div></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" style="margin-left: 96px;"><div class="line" lang="c" id="LC631"><span class="">}</span></div>
<div class="line" lang="c" id="LC632"></div>
<div class="line" lang="c" id="LC633"><span class="hljs-type">int</span><span class=""> </span><span class="hljs-title.function">zmodem_send_znak</span><span class="hljs-params"><span class="hljs-params">(</span><span class="hljs-type">zmodem_t</span><span class="hljs-params">* zm)</span></span></div>
<div class="line" lang="c" id="LC634"><span class="">{</span></div>
<div class="line" lang="c" id="LC635"><span class="">	lprintf</span><span class="">(zm, LOG_INFO, </span><span class="hljs-string">"%lu Sending ZNAK"</span><span class="">, </span><span class="">(ulong)</span><span class="">zm-&gt;current_file_pos)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC636"><span class="">	</span><span class="hljs-keyword">return</span><span class=""> zmodem_send_pos_header</span><span class="">(zm, ZNAK, </span><span class="hljs-number">0</span><span class="">, </span><span class="hljs-comment">/* Hex? */</span><span class=""> TRUE)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC637"><span class="">}</span></div>
<div class="line" lang="c" id="LC638"></div>
<div class="line" lang="c" id="LC639"><span class="hljs-type">int</span><span class=""> </span><span class="hljs-title.function">zmodem_send_zskip</span><span class="hljs-params"><span class="hljs-params">(</span><span class="hljs-type">zmodem_t</span><span class="hljs-params">* zm)</span></span></div>
<div class="line" lang="c" id="LC640"><span class="">{</span></div>
<div class="line" lang="c" id="LC641"><span class="">	lprintf</span><span class="">(zm, LOG_INFO, </span><span class="hljs-string">"%lu Sending ZSKIP"</span><span class="">, </span><span class="">(ulong)</span><span class="">zm-&gt;current_file_pos)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC642"><span class="">	</span><span class="hljs-keyword">return</span><span class=""> zmodem_send_pos_header</span><span class="">(zm, ZSKIP, </span><span class="hljs-number">0L</span><span class="">, </span><span class="hljs-comment">/* Hex? */</span><span class=""> TRUE)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC643"><span class="">}</span></div>
<div class="line" lang="c" id="LC644"></div>
<div class="line" lang="c" id="LC645"><span class="hljs-type">int</span><span class=""> </span><span class="hljs-title.function">zmodem_send_zeof</span><span class="hljs-params"><span class="hljs-params">(</span><span class="hljs-type">zmodem_t</span><span class="hljs-params">* zm)</span></span></div>
<div class="line" lang="c" id="LC646"><span class="">{</span></div>
<div class="line" lang="c" id="LC647"><span class="">	lprintf</span><span class="">(zm, LOG_INFO, </span><span class="hljs-string">"%lu Sending End-of-File (ZEOF) frame"</span><span class="">, </span><span class="">(ulong)</span><span class="">zm-&gt;current_file_pos)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC648"><span class="">	</span><span class="hljs-keyword">return</span><span class=""> zmodem_send_pos_header</span><span class="">(zm, ZEOF, </span><span class="">(</span><span class="hljs-type">int32_t</span><span class="">)</span><span class="">zm-&gt;current_file_pos, </span><span class="hljs-comment">/* Hex? */</span><span class=""> TRUE)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC649"><span class="">}</span></div>
<div class="line" lang="c" id="LC650"></div>
<div class="line" lang="c" id="LC651"></div>
<div class="line" lang="c" id="LC652"><span class="hljs-comment"><span class="hljs-comment">/*</span></span></div>
<div class="line" lang="c" id="LC653"><span class="hljs-comment"> * rx_raw ;</span><span class="hljs-comment"> receive a single </span><span class="hljs-comment">byte from the line.</span></div>
<div class="line" lang="c" id="LC654"><span class="hljs-comment"> * reads as</span><span class="hljs-comment"> many are available </span><span class="hljs-comment">and</span><span class="hljs-comment"> then processes them </span><span class="hljs-comment">one at a time</span></div>
<div class="line" lang="c" id="LC655"><span class="hljs-comment"> *</span><span class="hljs-comment"> check the data </span><span class="hljs-comment">stream for 5 consecutive CAN characters;</span></div>
<div class="line" lang="c" id="LC656"><span class="hljs-comment"> *</span><span class="hljs-comment"> and if you </span><span class="hljs-comment">see</span><span class="hljs-comment"> them abort. this </span><span class="hljs-comment">saves a lot of clutter in</span></div>
<div class="line" lang="c" id="LC657"><span class="hljs-comment"> * the rest of the code;</span><span class="hljs-comment"> even though it </span><span class="hljs-comment">is</span><span class="hljs-comment"> a very strange </span><span class="hljs-comment">place</span></div>
<div class="line" lang="c" id="LC658"><span class="hljs-comment"> * for an exit. (but</span><span class="hljs-comment"> that was what </span><span class="hljs-comment">session</span><span class="hljs-comment"> abort was all </span><span class="hljs-comment">about.)</span></div>
<div class="line" lang="c" id="LC659"><span class="hljs-comment"> */</span></div>
<div class="line" lang="c" id="LC660"></div>
<div class="line" lang="c" id="LC661"><span class="hljs-type">int</span><span class=""> </span><span class="hljs-title.function">zmodem_recv_raw</span><span class="hljs-params"><span class="hljs-params">(</span><span class="hljs-type">zmodem_t</span><span class="hljs-params">* zm)</span></span></div>
<div class="line" lang="c" id="LC662"><span class="">{</span></div>
<div class="line" lang="c" id="LC663"><span class="">	</span><span class="hljs-type">int</span><span class="">      c </span><span class="">= NOINP;</span></div>
<div class="line" lang="c" id="LC664"><span class="">	</span><span class="hljs-type">unsigned</span><span class=""> attempt;</span></div>
<div class="line" lang="c" id="LC665"></div>
<div class="line" lang="c" id="LC666"><span class="">	</span><span class="hljs-keyword">for</span><span class=""> </span><span class="">(attempt = </span><span class="hljs-number">0</span><span class="">; attempt &lt; zm-&gt;recv_timeout; attempt++)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC667"><span class="">		</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(</span><span class="">(c = zm-&gt;recv_byte</span><span class="">(zm-&gt;cbdata, </span><span class="hljs-number">1</span><span class=""> </span><span class="hljs-comment">/* second timeout */</span><span class="">)</span><span class="">)</span><span class=""> &gt;= </span><span class="hljs-number">0</span><span class="">)</span></div>
<div class="line" lang="c" id="LC668"><span class="">			</span><span class="hljs-keyword">break</span><span class="">;</span></div>
<div class="line" lang="c" id="LC669"><span class="">		</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(is_cancelled</span><span class="">(zm)</span><span class="">)</span></div>
<div class="line" lang="c" id="LC670"><span class="">			</span><span class="hljs-keyword">return</span><span class=""> ZCAN;</span></div>
<div class="line" lang="c" id="LC671"><span class="">		</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(!is_connected</span><span class="">(zm)</span><span class="">)</span></div>
<div class="line" lang="c" id="LC672"><span class="">			</span><span class="hljs-keyword">return</span><span class=""> ABORTED;</span></div>
<div class="line" lang="c" id="LC673"><span class="">		lprintf</span><span class="">(zm, LOG_DEBUG, </span><span class="hljs-string">"%s Received NO INPUT (attempt %u of %u)"</span></div>
<div class="line" lang="c" id="LC674"><span class="">		        , __FUNCTION__, attempt + </span><span class="hljs-number">1</span><span class="">, zm-&gt;recv_timeout)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC675"><span class="">	}</span></div>
<div class="line" lang="c" id="LC676"><span class="">	</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(attempt &gt;= zm-&gt;recv_timeout)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC677"><span class="">		lprintf</span><span class="">(zm, LOG_WARNING, </span><span class="hljs-string">"%lu %s TIMEOUT (%u seconds)"</span></div>
<div class="line" lang="c" id="LC678"><span class="">		        , </span><span class="">(ulong)</span><span class="">zm-&gt;current_file_pos, __FUNCTION__, attempt)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC679"><span class="">		</span><span class="hljs-keyword">return</span><span class=""> TIMEOUT;</span></div>
<div class="line" lang="c" id="LC680"><span class="">	}</span></div>
<div class="line" lang="c" id="LC681"></div>
<div class="line" lang="c" id="LC682"><span class="">	</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(c == CAN)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC683"><span class="">		zm-&gt;n_cans++;</span></div>
<div class="line" lang="c" id="LC684"><span class="">		</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(zm-&gt;n_cans == </span><span class="hljs-number">5</span><span class="">)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC685"><span class="">			zm-&gt;cancelled </span><span class="">= TRUE;</span></div>
<div class="line" lang="c" id="LC686"><span class="">			lprintf</span><span class="">(zm, LOG_WARNING, </span><span class="hljs-string">"%lu Canceled remotely"</span><span class="">, </span><span class="">(ulong)</span><span class="">zm-&gt;current_file_pos)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC687"><span class="hljs-comment">/*			return(TIMEOUT);	removed June-12-2005 */</span></div>
<div class="line" lang="c" id="LC688"><span class="">		}</span></div>
<div class="line" lang="c" id="LC689"><span class="">	}</span></div>
<div class="line" lang="c" id="LC690"><span class="">	</span><span class="hljs-keyword">else</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC691"><span class="">		zm-&gt;n_cans = </span><span class="hljs-number">0</span><span class="">;</span></div>
<div class="line" lang="c" id="LC692"><span class="">	}</span></div>
<div class="line" lang="c" id="LC693"></div>
<div class="line" lang="c" id="LC694"><span class="">	</span><span class="hljs-keyword">return</span><span class=""> c;</span></div>
<div class="line" lang="c" id="LC695"><span class="">}</span></div>
<div class="line" lang="c" id="LC696"></div>
<div class="line" lang="c" id="LC697"><span class="hljs-comment"><span class="hljs-comment">/*</span></span></div>
<div class="line" lang="c" id="LC698"><span class="hljs-comment"> * rx;</span><span class="hljs-comment"> receive a single </span><span class="hljs-comment">byte</span><span class="hljs-comment"> undoing any escaping </span><span class="hljs-comment">at the</span></div>
<div class="line" lang="c" id="LC699"><span class="hljs-comment"> *</span><span class="hljs-comment"> sending site. this </span><span class="hljs-comment">bit</span><span class="hljs-comment"> looks like a </span><span class="hljs-comment">mess. sorry for that</span></div>
<div class="line" lang="c" id="LC700"><span class="hljs-comment"> *</span><span class="hljs-comment"> but there seems </span><span class="hljs-comment">to be no</span><span class="hljs-comment"> other way without </span><span class="hljs-comment">incurring a lot</span></div></code></pre></div></div><div class="gl-flex"><div class="gl-absolute gl-flex gl-flex-col"><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L701" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L701" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L701" data-line-number="701" class="file-line-num gl-select-none !gl-shadow-none">
        701
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L702" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L702" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L702" data-line-number="702" class="file-line-num gl-select-none !gl-shadow-none">
        702
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L703" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L703" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L703" data-line-number="703" class="file-line-num gl-select-none !gl-shadow-none">
        703
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L704" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L704" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L704" data-line-number="704" class="file-line-num gl-select-none !gl-shadow-none">
        704
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L705" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L705" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L705" data-line-number="705" class="file-line-num gl-select-none !gl-shadow-none">
        705
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L706" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L706" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L706" data-line-number="706" class="file-line-num gl-select-none !gl-shadow-none">
        706
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L707" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L707" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L707" data-line-number="707" class="file-line-num gl-select-none !gl-shadow-none">
        707
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L708" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L708" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L708" data-line-number="708" class="file-line-num gl-select-none !gl-shadow-none">
        708
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L709" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L709" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L709" data-line-number="709" class="file-line-num gl-select-none !gl-shadow-none">
        709
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L710" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L710" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L710" data-line-number="710" class="file-line-num gl-select-none !gl-shadow-none">
        710
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L711" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L711" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L711" data-line-number="711" class="file-line-num gl-select-none !gl-shadow-none">
        711
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L712" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L712" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L712" data-line-number="712" class="file-line-num gl-select-none !gl-shadow-none">
        712
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L713" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L713" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L713" data-line-number="713" class="file-line-num gl-select-none !gl-shadow-none">
        713
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L714" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L714" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L714" data-line-number="714" class="file-line-num gl-select-none !gl-shadow-none">
        714
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L715" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L715" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L715" data-line-number="715" class="file-line-num gl-select-none !gl-shadow-none">
        715
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L716" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L716" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L716" data-line-number="716" class="file-line-num gl-select-none !gl-shadow-none">
        716
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L717" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L717" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L717" data-line-number="717" class="file-line-num gl-select-none !gl-shadow-none">
        717
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L718" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L718" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L718" data-line-number="718" class="file-line-num gl-select-none !gl-shadow-none">
        718
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L719" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L719" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L719" data-line-number="719" class="file-line-num gl-select-none !gl-shadow-none">
        719
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L720" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L720" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L720" data-line-number="720" class="file-line-num gl-select-none !gl-shadow-none">
        720
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L721" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L721" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L721" data-line-number="721" class="file-line-num gl-select-none !gl-shadow-none">
        721
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L722" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L722" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L722" data-line-number="722" class="file-line-num gl-select-none !gl-shadow-none">
        722
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L723" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L723" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L723" data-line-number="723" class="file-line-num gl-select-none !gl-shadow-none">
        723
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L724" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L724" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L724" data-line-number="724" class="file-line-num gl-select-none !gl-shadow-none">
        724
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L725" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L725" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L725" data-line-number="725" class="file-line-num gl-select-none !gl-shadow-none">
        725
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L726" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L726" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L726" data-line-number="726" class="file-line-num gl-select-none !gl-shadow-none">
        726
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L727" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L727" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L727" data-line-number="727" class="file-line-num gl-select-none !gl-shadow-none">
        727
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L728" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L728" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L728" data-line-number="728" class="file-line-num gl-select-none !gl-shadow-none">
        728
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L729" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L729" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L729" data-line-number="729" class="file-line-num gl-select-none !gl-shadow-none">
        729
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L730" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L730" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L730" data-line-number="730" class="file-line-num gl-select-none !gl-shadow-none">
        730
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L731" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L731" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L731" data-line-number="731" class="file-line-num gl-select-none !gl-shadow-none">
        731
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L732" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L732" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L732" data-line-number="732" class="file-line-num gl-select-none !gl-shadow-none">
        732
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L733" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L733" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L733" data-line-number="733" class="file-line-num gl-select-none !gl-shadow-none">
        733
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L734" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L734" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L734" data-line-number="734" class="file-line-num gl-select-none !gl-shadow-none">
        734
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L735" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L735" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L735" data-line-number="735" class="file-line-num gl-select-none !gl-shadow-none">
        735
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L736" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L736" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L736" data-line-number="736" class="file-line-num gl-select-none !gl-shadow-none">
        736
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L737" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L737" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L737" data-line-number="737" class="file-line-num gl-select-none !gl-shadow-none">
        737
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L738" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L738" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L738" data-line-number="738" class="file-line-num gl-select-none !gl-shadow-none">
        738
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L739" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L739" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L739" data-line-number="739" class="file-line-num gl-select-none !gl-shadow-none">
        739
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L740" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L740" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L740" data-line-number="740" class="file-line-num gl-select-none !gl-shadow-none">
        740
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L741" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L741" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L741" data-line-number="741" class="file-line-num gl-select-none !gl-shadow-none">
        741
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L742" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L742" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L742" data-line-number="742" class="file-line-num gl-select-none !gl-shadow-none">
        742
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L743" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L743" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L743" data-line-number="743" class="file-line-num gl-select-none !gl-shadow-none">
        743
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L744" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L744" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L744" data-line-number="744" class="file-line-num gl-select-none !gl-shadow-none">
        744
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L745" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L745" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L745" data-line-number="745" class="file-line-num gl-select-none !gl-shadow-none">
        745
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L746" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L746" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L746" data-line-number="746" class="file-line-num gl-select-none !gl-shadow-none">
        746
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L747" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L747" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L747" data-line-number="747" class="file-line-num gl-select-none !gl-shadow-none">
        747
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L748" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L748" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L748" data-line-number="748" class="file-line-num gl-select-none !gl-shadow-none">
        748
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L749" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L749" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L749" data-line-number="749" class="file-line-num gl-select-none !gl-shadow-none">
        749
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L750" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L750" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L750" data-line-number="750" class="file-line-num gl-select-none !gl-shadow-none">
        750
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L751" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L751" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L751" data-line-number="751" class="file-line-num gl-select-none !gl-shadow-none">
        751
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L752" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L752" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L752" data-line-number="752" class="file-line-num gl-select-none !gl-shadow-none">
        752
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L753" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L753" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L753" data-line-number="753" class="file-line-num gl-select-none !gl-shadow-none">
        753
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L754" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L754" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L754" data-line-number="754" class="file-line-num gl-select-none !gl-shadow-none">
        754
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L755" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L755" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L755" data-line-number="755" class="file-line-num gl-select-none !gl-shadow-none">
        755
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L756" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L756" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L756" data-line-number="756" class="file-line-num gl-select-none !gl-shadow-none">
        756
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L757" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L757" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L757" data-line-number="757" class="file-line-num gl-select-none !gl-shadow-none">
        757
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L758" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L758" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L758" data-line-number="758" class="file-line-num gl-select-none !gl-shadow-none">
        758
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L759" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L759" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L759" data-line-number="759" class="file-line-num gl-select-none !gl-shadow-none">
        759
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L760" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L760" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L760" data-line-number="760" class="file-line-num gl-select-none !gl-shadow-none">
        760
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L761" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L761" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L761" data-line-number="761" class="file-line-num gl-select-none !gl-shadow-none">
        761
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L762" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L762" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L762" data-line-number="762" class="file-line-num gl-select-none !gl-shadow-none">
        762
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L763" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L763" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L763" data-line-number="763" class="file-line-num gl-select-none !gl-shadow-none">
        763
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L764" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L764" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L764" data-line-number="764" class="file-line-num gl-select-none !gl-shadow-none">
        764
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L765" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L765" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L765" data-line-number="765" class="file-line-num gl-select-none !gl-shadow-none">
        765
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L766" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L766" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L766" data-line-number="766" class="file-line-num gl-select-none !gl-shadow-none">
        766
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L767" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L767" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L767" data-line-number="767" class="file-line-num gl-select-none !gl-shadow-none">
        767
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L768" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L768" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L768" data-line-number="768" class="file-line-num gl-select-none !gl-shadow-none">
        768
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L769" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L769" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L769" data-line-number="769" class="file-line-num gl-select-none !gl-shadow-none">
        769
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L770" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L770" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L770" data-line-number="770" class="file-line-num gl-select-none !gl-shadow-none">
        770
      </a></div></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" style="margin-left: 96px;"><div class="line" lang="c" id="LC701"><span class="hljs-comment"> * of</span><span class="hljs-comment"> overhead. at least </span><span class="hljs-comment">like</span><span class="hljs-comment"> this the path </span><span class="hljs-comment">for a normal character</span></div>
<div class="line" lang="c" id="LC702"><span class="hljs-comment"> * is relatively short.</span></div>
<div class="line" lang="c" id="LC703"><span class="hljs-comment"> */</span></div>
<div class="line" lang="c" id="LC704"></div>
<div class="line" lang="c" id="LC705"><span class="hljs-type">int</span><span class=""> </span><span class="hljs-title.function">zmodem_rx</span><span class="hljs-params"><span class="hljs-params">(</span><span class="hljs-type">zmodem_t</span><span class="hljs-params">* zm)</span></span></div>
<div class="line" lang="c" id="LC706"><span class="">{</span></div>
<div class="line" lang="c" id="LC707"><span class="">	</span><span class="hljs-type">int</span><span class=""> c;</span></div>
<div class="line" lang="c" id="LC708"></div>
<div class="line" lang="c" id="LC709"><span class="">	</span><span class="hljs-comment"><span class="hljs-comment">/*</span></span></div>
<div class="line" lang="c" id="LC710"><span class="hljs-comment">	 *</span><span class="hljs-comment"> outer loop for </span><span class="hljs-comment">ever</span><span class="hljs-comment"> so for sure </span><span class="hljs-comment">something valid</span></div>
<div class="line" lang="c" id="LC711"><span class="hljs-comment">	 * will come in;</span><span class="hljs-comment"> a timeout will </span><span class="hljs-comment">occur or a session abort</span></div>
<div class="line" lang="c" id="LC712"><span class="hljs-comment">	 * will be received.</span></div>
<div class="line" lang="c" id="LC713"><span class="hljs-comment">	 */</span></div>
<div class="line" lang="c" id="LC714"></div>
<div class="line" lang="c" id="LC715"><span class="">	</span><span class="hljs-keyword">while</span><span class=""> </span><span class="">(is_connected</span><span class="">(zm)</span><span class=""> &amp;&amp; !is_cancelled</span><span class="">(zm)</span><span class="">)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC716"></div>
<div class="line" lang="c" id="LC717"><span class="">		</span><span class="hljs-keyword">do</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC718"><span class="">			</span><span class="hljs-keyword">switch</span><span class=""> </span><span class="">(c = zmodem_recv_raw</span><span class="">(zm)</span><span class="">)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC719"><span class="">				</span><span class="hljs-keyword">case</span><span class=""> ZDLE:</span></div>
<div class="line" lang="c" id="LC720"><span class="">					</span><span class="hljs-keyword">break</span><span class="">;</span></div>
<div class="line" lang="c" id="LC721"><span class="">				</span><span class="hljs-keyword">case</span><span class=""> XON:</span></div>
<div class="line" lang="c" id="LC722"><span class="">				</span><span class="hljs-keyword">case</span><span class=""> XON | </span><span class="hljs-number">0x80</span><span class="">:</span></div>
<div class="line" lang="c" id="LC723"><span class="">				</span><span class="hljs-keyword">case</span><span class=""> XOFF:</span></div>
<div class="line" lang="c" id="LC724"><span class="">				</span><span class="hljs-keyword">case</span><span class=""> XOFF | </span><span class="hljs-number">0x80</span><span class="">:</span></div>
<div class="line" lang="c" id="LC725"><span class="">					lprintf</span><span class="">(zm, LOG_WARNING, </span><span class="hljs-string">"%lu Dropping flow ctrl char: %s"</span></div>
<div class="line" lang="c" id="LC726"><span class="">					        , </span><span class="">(ulong)</span><span class="">zm-&gt;current_file_pos, chr</span><span class="">(c)</span><span class="">)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC727"><span class="">					</span><span class="hljs-keyword">continue</span><span class="">;</span></div>
<div class="line" lang="c" id="LC728"><span class="">				</span><span class="hljs-keyword">default</span><span class="">:</span></div>
<div class="line" lang="c" id="LC729"><span class="">					</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(c &lt; </span><span class="hljs-number">0</span><span class="">)</span></div>
<div class="line" lang="c" id="LC730"><span class="">						</span><span class="hljs-keyword">return</span><span class=""> c;</span></div>
<div class="line" lang="c" id="LC731"><span class="">					</span><span class="hljs-comment"><span class="hljs-comment">/*</span></span></div>
<div class="line" lang="c" id="LC732"><span class="hljs-comment">					 *</span><span class="hljs-comment"> if all control </span><span class="hljs-comment">characters should be escaped and</span></div>
<div class="line" lang="c" id="LC733"><span class="hljs-comment">					 *</span><span class="hljs-comment"> this one wasn't </span><span class="hljs-comment">then</span><span class="hljs-comment"> its spurious and </span><span class="hljs-comment">should be dropped.</span></div>
<div class="line" lang="c" id="LC734"><span class="hljs-comment">					 */</span></div>
<div class="line" lang="c" id="LC735"><span class="">					</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(zm-&gt;escape_ctrl_chars &amp;&amp; </span><span class="">(c &gt;= </span><span class="hljs-number">0</span><span class="">)</span><span class=""> &amp;&amp; </span><span class="">(c &amp; </span><span class="hljs-number">0x60</span><span class="">)</span><span class=""> == </span><span class="hljs-number">0</span><span class="">)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC736"><span class="">						lprintf</span><span class="">(zm, LOG_WARNING, </span><span class="hljs-string">"%lu Dropping unescaped ctrl char: %s"</span></div>
<div class="line" lang="c" id="LC737"><span class="">						        , </span><span class="">(ulong)</span><span class="">zm-&gt;current_file_pos, chr</span><span class="">(c)</span><span class="">)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC738"><span class="">						</span><span class="hljs-keyword">continue</span><span class="">;</span></div>
<div class="line" lang="c" id="LC739"><span class="">					}</span></div>
<div class="line" lang="c" id="LC740"><span class="">					</span><span class="hljs-comment">/*</span></div>
<div class="line" lang="c" id="LC741"><span class="hljs-comment">					 * normal character; return it.</span></div>
<div class="line" lang="c" id="LC742"><span class="hljs-comment">					 */</span></div>
<div class="line" lang="c" id="LC743"><span class="">					</span><span class="hljs-keyword">return</span><span class=""> c;</span></div>
<div class="line" lang="c" id="LC744"><span class="">			}</span></div>
<div class="line" lang="c" id="LC745"><span class="">			</span><span class="hljs-keyword">break</span><span class="">;</span></div>
<div class="line" lang="c" id="LC746"><span class="">		} </span><span class="hljs-keyword">while</span><span class=""> </span><span class="">(!is_cancelled</span><span class="">(zm)</span><span class="">)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC747"></div>
<div class="line" lang="c" id="LC748"><span class="">		</span><span class="hljs-comment"><span class="hljs-comment">/*</span></span></div>
<div class="line" lang="c" id="LC749"><span class="hljs-comment">		 * ZDLE encoded sequence or session abort.</span></div>
<div class="line" lang="c" id="LC750"><span class="hljs-comment">		 * (or something illegal;</span><span class="hljs-comment"> then back to </span><span class="hljs-comment">the top)</span></div>
<div class="line" lang="c" id="LC751"><span class="hljs-comment">		 */</span></div>
<div class="line" lang="c" id="LC752"></div>
<div class="line" lang="c" id="LC753"><span class="">		</span><span class="hljs-keyword">while</span><span class=""> </span><span class="">(!is_cancelled</span><span class="">(zm)</span><span class="">)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC754"></div>
<div class="line" lang="c" id="LC755"><span class="">			</span><span class="hljs-keyword">switch</span><span class=""> </span><span class="">(c = zmodem_recv_raw</span><span class="">(zm)</span><span class="">)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC756"><span class="">				</span><span class="hljs-keyword">case</span><span class=""> XON:</span></div>
<div class="line" lang="c" id="LC757"><span class="">				</span><span class="hljs-keyword">case</span><span class=""> XON | </span><span class="hljs-number">0x80</span><span class="">:</span></div>
<div class="line" lang="c" id="LC758"><span class="">				</span><span class="hljs-keyword">case</span><span class=""> XOFF:</span></div>
<div class="line" lang="c" id="LC759"><span class="">				</span><span class="hljs-keyword">case</span><span class=""> XOFF | </span><span class="hljs-number">0x80</span><span class="">:</span></div>
<div class="line" lang="c" id="LC760"><span class="">				</span><span class="hljs-keyword">case</span><span class=""> ZDLE:</span></div>
<div class="line" lang="c" id="LC761"><span class="">					lprintf</span><span class="">(zm, LOG_WARNING, </span><span class="hljs-string">"%lu Dropping escaped flow ctrl char: %s"</span></div>
<div class="line" lang="c" id="LC762"><span class="">					        , </span><span class="">(ulong)</span><span class="">zm-&gt;current_file_pos, chr</span><span class="">(c)</span><span class="">)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC763"><span class="">					</span><span class="hljs-keyword">continue</span><span class="">;</span></div>
<div class="line" lang="c" id="LC764"><span class="">				</span><span class="hljs-comment"><span class="hljs-comment">/*</span></span></div>
<div class="line" lang="c" id="LC765"><span class="hljs-comment">				 *</span><span class="hljs-comment"> these four are </span><span class="hljs-comment">really nasty.</span></div>
<div class="line" lang="c" id="LC766"><span class="hljs-comment">				 * for convenience we</span><span class="hljs-comment"> just change them </span><span class="hljs-comment">into</span></div>
<div class="line" lang="c" id="LC767"><span class="hljs-comment">				 * special characters by</span><span class="hljs-comment"> setting a bit </span><span class="hljs-comment">outside the</span></div>
<div class="line" lang="c" id="LC768"><span class="hljs-comment">				 * first 8.</span><span class="hljs-comment"> that way they </span><span class="hljs-comment">can be recognized and still</span></div>
<div class="line" lang="c" id="LC769"><span class="hljs-comment">				 * be processed as characters by the rest of the code.</span></div>
<div class="line" lang="c" id="LC770"><span class="hljs-comment">				 */</span></div></code></pre></div></div><div class="gl-flex"><div class="gl-absolute gl-flex gl-flex-col"><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L771" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L771" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L771" data-line-number="771" class="file-line-num gl-select-none !gl-shadow-none">
        771
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L772" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L772" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L772" data-line-number="772" class="file-line-num gl-select-none !gl-shadow-none">
        772
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L773" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L773" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L773" data-line-number="773" class="file-line-num gl-select-none !gl-shadow-none">
        773
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L774" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L774" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L774" data-line-number="774" class="file-line-num gl-select-none !gl-shadow-none">
        774
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L775" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L775" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L775" data-line-number="775" class="file-line-num gl-select-none !gl-shadow-none">
        775
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L776" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L776" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L776" data-line-number="776" class="file-line-num gl-select-none !gl-shadow-none">
        776
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L777" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L777" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L777" data-line-number="777" class="file-line-num gl-select-none !gl-shadow-none">
        777
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L778" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L778" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L778" data-line-number="778" class="file-line-num gl-select-none !gl-shadow-none">
        778
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L779" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L779" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L779" data-line-number="779" class="file-line-num gl-select-none !gl-shadow-none">
        779
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L780" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L780" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L780" data-line-number="780" class="file-line-num gl-select-none !gl-shadow-none">
        780
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L781" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L781" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L781" data-line-number="781" class="file-line-num gl-select-none !gl-shadow-none">
        781
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L782" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L782" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L782" data-line-number="782" class="file-line-num gl-select-none !gl-shadow-none">
        782
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L783" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L783" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L783" data-line-number="783" class="file-line-num gl-select-none !gl-shadow-none">
        783
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L784" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L784" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L784" data-line-number="784" class="file-line-num gl-select-none !gl-shadow-none">
        784
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L785" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L785" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L785" data-line-number="785" class="file-line-num gl-select-none !gl-shadow-none">
        785
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L786" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L786" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L786" data-line-number="786" class="file-line-num gl-select-none !gl-shadow-none">
        786
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L787" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L787" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L787" data-line-number="787" class="file-line-num gl-select-none !gl-shadow-none">
        787
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L788" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L788" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L788" data-line-number="788" class="file-line-num gl-select-none !gl-shadow-none">
        788
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L789" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L789" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L789" data-line-number="789" class="file-line-num gl-select-none !gl-shadow-none">
        789
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L790" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L790" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L790" data-line-number="790" class="file-line-num gl-select-none !gl-shadow-none">
        790
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L791" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L791" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L791" data-line-number="791" class="file-line-num gl-select-none !gl-shadow-none">
        791
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L792" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L792" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L792" data-line-number="792" class="file-line-num gl-select-none !gl-shadow-none">
        792
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L793" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L793" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L793" data-line-number="793" class="file-line-num gl-select-none !gl-shadow-none">
        793
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L794" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L794" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L794" data-line-number="794" class="file-line-num gl-select-none !gl-shadow-none">
        794
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L795" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L795" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L795" data-line-number="795" class="file-line-num gl-select-none !gl-shadow-none">
        795
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L796" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L796" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L796" data-line-number="796" class="file-line-num gl-select-none !gl-shadow-none">
        796
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L797" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L797" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L797" data-line-number="797" class="file-line-num gl-select-none !gl-shadow-none">
        797
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L798" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L798" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L798" data-line-number="798" class="file-line-num gl-select-none !gl-shadow-none">
        798
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L799" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L799" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L799" data-line-number="799" class="file-line-num gl-select-none !gl-shadow-none">
        799
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L800" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L800" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L800" data-line-number="800" class="file-line-num gl-select-none !gl-shadow-none">
        800
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L801" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L801" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L801" data-line-number="801" class="file-line-num gl-select-none !gl-shadow-none">
        801
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L802" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L802" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L802" data-line-number="802" class="file-line-num gl-select-none !gl-shadow-none">
        802
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L803" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L803" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L803" data-line-number="803" class="file-line-num gl-select-none !gl-shadow-none">
        803
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L804" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L804" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L804" data-line-number="804" class="file-line-num gl-select-none !gl-shadow-none">
        804
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L805" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L805" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L805" data-line-number="805" class="file-line-num gl-select-none !gl-shadow-none">
        805
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L806" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L806" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L806" data-line-number="806" class="file-line-num gl-select-none !gl-shadow-none">
        806
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L807" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L807" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L807" data-line-number="807" class="file-line-num gl-select-none !gl-shadow-none">
        807
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L808" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L808" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L808" data-line-number="808" class="file-line-num gl-select-none !gl-shadow-none">
        808
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L809" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L809" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L809" data-line-number="809" class="file-line-num gl-select-none !gl-shadow-none">
        809
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L810" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L810" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L810" data-line-number="810" class="file-line-num gl-select-none !gl-shadow-none">
        810
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L811" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L811" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L811" data-line-number="811" class="file-line-num gl-select-none !gl-shadow-none">
        811
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L812" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L812" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L812" data-line-number="812" class="file-line-num gl-select-none !gl-shadow-none">
        812
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L813" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L813" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L813" data-line-number="813" class="file-line-num gl-select-none !gl-shadow-none">
        813
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L814" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L814" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L814" data-line-number="814" class="file-line-num gl-select-none !gl-shadow-none">
        814
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L815" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L815" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L815" data-line-number="815" class="file-line-num gl-select-none !gl-shadow-none">
        815
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L816" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L816" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L816" data-line-number="816" class="file-line-num gl-select-none !gl-shadow-none">
        816
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L817" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L817" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L817" data-line-number="817" class="file-line-num gl-select-none !gl-shadow-none">
        817
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L818" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L818" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L818" data-line-number="818" class="file-line-num gl-select-none !gl-shadow-none">
        818
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L819" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L819" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L819" data-line-number="819" class="file-line-num gl-select-none !gl-shadow-none">
        819
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L820" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L820" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L820" data-line-number="820" class="file-line-num gl-select-none !gl-shadow-none">
        820
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L821" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L821" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L821" data-line-number="821" class="file-line-num gl-select-none !gl-shadow-none">
        821
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L822" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L822" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L822" data-line-number="822" class="file-line-num gl-select-none !gl-shadow-none">
        822
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L823" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L823" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L823" data-line-number="823" class="file-line-num gl-select-none !gl-shadow-none">
        823
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L824" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L824" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L824" data-line-number="824" class="file-line-num gl-select-none !gl-shadow-none">
        824
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L825" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L825" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L825" data-line-number="825" class="file-line-num gl-select-none !gl-shadow-none">
        825
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L826" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L826" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L826" data-line-number="826" class="file-line-num gl-select-none !gl-shadow-none">
        826
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L827" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L827" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L827" data-line-number="827" class="file-line-num gl-select-none !gl-shadow-none">
        827
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L828" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L828" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L828" data-line-number="828" class="file-line-num gl-select-none !gl-shadow-none">
        828
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L829" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L829" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L829" data-line-number="829" class="file-line-num gl-select-none !gl-shadow-none">
        829
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L830" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L830" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L830" data-line-number="830" class="file-line-num gl-select-none !gl-shadow-none">
        830
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L831" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L831" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L831" data-line-number="831" class="file-line-num gl-select-none !gl-shadow-none">
        831
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L832" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L832" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L832" data-line-number="832" class="file-line-num gl-select-none !gl-shadow-none">
        832
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L833" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L833" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L833" data-line-number="833" class="file-line-num gl-select-none !gl-shadow-none">
        833
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L834" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L834" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L834" data-line-number="834" class="file-line-num gl-select-none !gl-shadow-none">
        834
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L835" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L835" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L835" data-line-number="835" class="file-line-num gl-select-none !gl-shadow-none">
        835
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L836" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L836" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L836" data-line-number="836" class="file-line-num gl-select-none !gl-shadow-none">
        836
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L837" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L837" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L837" data-line-number="837" class="file-line-num gl-select-none !gl-shadow-none">
        837
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L838" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L838" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L838" data-line-number="838" class="file-line-num gl-select-none !gl-shadow-none">
        838
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L839" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L839" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L839" data-line-number="839" class="file-line-num gl-select-none !gl-shadow-none">
        839
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L840" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L840" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L840" data-line-number="840" class="file-line-num gl-select-none !gl-shadow-none">
        840
      </a></div></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" style="margin-left: 96px;"><div class="line" lang="c" id="LC771"><span class="">				</span><span class="hljs-keyword">case</span><span class=""> ZCRCE:</span></div>
<div class="line" lang="c" id="LC772"><span class="">				</span><span class="hljs-keyword">case</span><span class=""> ZCRCG:</span></div>
<div class="line" lang="c" id="LC773"><span class="">				</span><span class="hljs-keyword">case</span><span class=""> ZCRCQ:</span></div>
<div class="line" lang="c" id="LC774"><span class="">				</span><span class="hljs-keyword">case</span><span class=""> ZCRCW:</span></div>
<div class="line" lang="c" id="LC775"><span class="hljs-comment"><span class="hljs-comment">//					lprintf(zm,LOG_DEBUG, "%lu</span><span class="hljs-comment"> Encoding data subpacket </span><span class="hljs-comment">type: %s", (ulong)zm-&gt;current_file_pos, chr(c));</span></span></div>
<div class="line" lang="c" id="LC776"><span class="">					</span><span class="hljs-keyword">return</span><span class=""> c | ZDLEESC;</span></div>
<div class="line" lang="c" id="LC777"><span class="">				</span><span class="hljs-keyword">case</span><span class=""> ZRUB0:</span></div>
<div class="line" lang="c" id="LC778"><span class="">					</span><span class="hljs-keyword">return</span><span class=""> </span><span class="hljs-number">0x7f</span><span class="">;</span></div>
<div class="line" lang="c" id="LC779"><span class="">				</span><span class="hljs-keyword">case</span><span class=""> ZRUB1:</span></div>
<div class="line" lang="c" id="LC780"><span class="">					</span><span class="hljs-keyword">return</span><span class=""> </span><span class="hljs-number">0xff</span><span class="">;</span></div>
<div class="line" lang="c" id="LC781"><span class="">				</span><span class="hljs-keyword">default</span><span class="">:</span></div>
<div class="line" lang="c" id="LC782"><span class="">					</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(c &lt; </span><span class="hljs-number">0</span><span class="">)</span></div>
<div class="line" lang="c" id="LC783"><span class="">						</span><span class="hljs-keyword">return</span><span class=""> c;</span></div>
<div class="line" lang="c" id="LC784"></div>
<div class="line" lang="c" id="LC785"><span class="">					</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(zm-&gt;escape_ctrl_chars &amp;&amp; </span><span class="">(c &amp; </span><span class="hljs-number">0x60</span><span class="">)</span><span class=""> == </span><span class="hljs-number">0</span><span class="">)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC786"><span class="">						</span><span class="hljs-comment"><span class="hljs-comment">/*</span></span></div>
<div class="line" lang="c" id="LC787"><span class="hljs-comment">						 *</span><span class="hljs-comment"> a not escaped </span><span class="hljs-comment">control character; probably</span></div>
<div class="line" lang="c" id="LC788"><span class="hljs-comment">						 *</span><span class="hljs-comment"> something from a </span><span class="hljs-comment">network. just drop it.</span></div>
<div class="line" lang="c" id="LC789"><span class="hljs-comment">						 */</span></div>
<div class="line" lang="c" id="LC790"><span class="">						lprintf</span><span class="">(zm, LOG_WARNING, </span><span class="hljs-string">"%lu Dropping unescaped ctrl char: %s"</span></div>
<div class="line" lang="c" id="LC791"><span class="">						        , </span><span class="">(ulong)</span><span class="">zm-&gt;current_file_pos, chr</span><span class="">(c)</span><span class="">)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC792"><span class="">						</span><span class="hljs-keyword">continue</span><span class="">;</span></div>
<div class="line" lang="c" id="LC793"><span class="">					}</span></div>
<div class="line" lang="c" id="LC794"><span class="">					</span><span class="hljs-comment"><span class="hljs-comment">/*</span></span></div>
<div class="line" lang="c" id="LC795"><span class="hljs-comment">					 * legitimate escape sequence.</span></div>
<div class="line" lang="c" id="LC796"><span class="hljs-comment">					 *</span><span class="hljs-comment"> rebuild the original </span><span class="hljs-comment">and return it.</span></div>
<div class="line" lang="c" id="LC797"><span class="hljs-comment">					 */</span></div>
<div class="line" lang="c" id="LC798"><span class="">					</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(</span><span class="">(c &amp; </span><span class="hljs-number">0x60</span><span class="">)</span><span class=""> == </span><span class="hljs-number">0x40</span><span class="">)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC799"><span class="">						</span><span class="hljs-keyword">return</span><span class=""> c ^ </span><span class="hljs-number">0x40</span><span class="">;</span></div>
<div class="line" lang="c" id="LC800"><span class="">					}</span></div>
<div class="line" lang="c" id="LC801"><span class="">					lprintf</span><span class="">(zm, LOG_WARNING, </span><span class="hljs-string">"%lu Illegal sequence: ZDLE %s"</span></div>
<div class="line" lang="c" id="LC802"><span class="">					        , </span><span class="">(ulong)</span><span class="">zm-&gt;current_file_pos, chr</span><span class="">(c)</span><span class="">)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC803"><span class="">					</span><span class="hljs-keyword">break</span><span class="">;</span></div>
<div class="line" lang="c" id="LC804"><span class="">			}</span></div>
<div class="line" lang="c" id="LC805"><span class="">			</span><span class="hljs-keyword">break</span><span class="">;</span></div>
<div class="line" lang="c" id="LC806"><span class="">		}</span></div>
<div class="line" lang="c" id="LC807"><span class="">	}</span></div>
<div class="line" lang="c" id="LC808"></div>
<div class="line" lang="c" id="LC809"><span class="">	</span><span class="hljs-comment">/*</span></div>
<div class="line" lang="c" id="LC810"><span class="hljs-comment">	 * not reached (unless canceled).</span></div>
<div class="line" lang="c" id="LC811"><span class="hljs-comment">	 */</span></div>
<div class="line" lang="c" id="LC812"></div>
<div class="line" lang="c" id="LC813"><span class="">	</span><span class="hljs-keyword">return</span><span class=""> ABORTED;</span></div>
<div class="line" lang="c" id="LC814"><span class="">}</span></div>
<div class="line" lang="c" id="LC815"></div>
<div class="line" lang="c" id="LC816"><span class="hljs-comment"><span class="hljs-comment">/*</span></span></div>
<div class="line" lang="c" id="LC817"><span class="hljs-comment"> *</span><span class="hljs-comment"> receive a data </span><span class="hljs-comment">subpacket as dictated by</span><span class="hljs-comment"> the last received </span><span class="hljs-comment">header.</span></div>
<div class="line" lang="c" id="LC818"><span class="hljs-comment"> * return 2</span><span class="hljs-comment"> with correct packet </span><span class="hljs-comment">and end of frame</span></div>
<div class="line" lang="c" id="LC819"><span class="hljs-comment"> * return 1</span><span class="hljs-comment"> with correct packet </span><span class="hljs-comment">frame continues</span></div>
<div class="line" lang="c" id="LC820"><span class="hljs-comment"> * return 0 with incorrect frame.</span></div>
<div class="line" lang="c" id="LC821"><span class="hljs-comment"> * return TIMEOUT with a timeout</span></div>
<div class="line" lang="c" id="LC822"><span class="hljs-comment"> * if an</span><span class="hljs-comment"> acknowledgment is requested </span><span class="hljs-comment">it is generated automatically</span></div>
<div class="line" lang="c" id="LC823"><span class="hljs-comment"> * here.</span></div>
<div class="line" lang="c" id="LC824"><span class="hljs-comment"> */</span></div>
<div class="line" lang="c" id="LC825"></div>
<div class="line" lang="c" id="LC826"><span class="hljs-comment">/*</span></div>
<div class="line" lang="c" id="LC827"><span class="hljs-comment"> * data subpacket reception</span></div>
<div class="line" lang="c" id="LC828"><span class="hljs-comment"> */</span></div>
<div class="line" lang="c" id="LC829"></div>
<div class="line" lang="c" id="LC830"><span class="hljs-type">int</span><span class=""> </span><span class="hljs-title.function">zmodem_recv_data32</span><span class="hljs-params"><span class="hljs-params">(</span><span class="hljs-type">zmodem_t</span><span class="hljs-params">* zm, </span><span class="hljs-type">unsigned</span><span class="hljs-params"> </span><span class="hljs-type">char</span><span class="hljs-params"> * p, </span><span class="hljs-type">unsigned</span><span class="hljs-params"> maxlen, </span><span class="hljs-type">unsigned</span><span class="hljs-params">* len, </span><span class="hljs-type">int</span><span class="hljs-params">* type)</span></span></div>
<div class="line" lang="c" id="LC831"><span class="">{</span></div>
<div class="line" lang="c" id="LC832"><span class="">	</span><span class="hljs-type">int</span><span class="">      c;</span></div>
<div class="line" lang="c" id="LC833"><span class="">	</span><span class="hljs-type">uint32_t</span><span class=""> rxd_crc;</span></div>
<div class="line" lang="c" id="LC834"><span class="">	</span><span class="hljs-type">uint32_t</span><span class=""> crc;</span></div>
<div class="line" lang="c" id="LC835"><span class="">	</span><span class="hljs-type">int</span><span class="">      subpkt_type;</span></div>
<div class="line" lang="c" id="LC836"></div>
<div class="line" lang="c" id="LC837"><span class="hljs-comment">//	lprintf(zm,LOG_DEBUG, __FUNCTION___);</span></div>
<div class="line" lang="c" id="LC838"></div>
<div class="line" lang="c" id="LC839"><span class="">	*type </span><span class="">= INVALIDSUBPKT;</span></div>
<div class="line" lang="c" id="LC840"><span class="">	crc </span><span class="">= </span><span class="hljs-number">0xffffffffl</span><span class="">;</span></div></code></pre></div></div><div class="gl-flex"><div class="gl-absolute gl-flex gl-flex-col"><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L841" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L841" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L841" data-line-number="841" class="file-line-num gl-select-none !gl-shadow-none">
        841
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L842" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L842" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L842" data-line-number="842" class="file-line-num gl-select-none !gl-shadow-none">
        842
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L843" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L843" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L843" data-line-number="843" class="file-line-num gl-select-none !gl-shadow-none">
        843
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L844" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L844" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L844" data-line-number="844" class="file-line-num gl-select-none !gl-shadow-none">
        844
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L845" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L845" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L845" data-line-number="845" class="file-line-num gl-select-none !gl-shadow-none">
        845
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L846" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L846" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L846" data-line-number="846" class="file-line-num gl-select-none !gl-shadow-none">
        846
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L847" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L847" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L847" data-line-number="847" class="file-line-num gl-select-none !gl-shadow-none">
        847
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L848" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L848" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L848" data-line-number="848" class="file-line-num gl-select-none !gl-shadow-none">
        848
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L849" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L849" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L849" data-line-number="849" class="file-line-num gl-select-none !gl-shadow-none">
        849
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L850" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L850" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L850" data-line-number="850" class="file-line-num gl-select-none !gl-shadow-none">
        850
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L851" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L851" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L851" data-line-number="851" class="file-line-num gl-select-none !gl-shadow-none">
        851
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L852" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L852" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L852" data-line-number="852" class="file-line-num gl-select-none !gl-shadow-none">
        852
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L853" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L853" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L853" data-line-number="853" class="file-line-num gl-select-none !gl-shadow-none">
        853
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L854" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L854" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L854" data-line-number="854" class="file-line-num gl-select-none !gl-shadow-none">
        854
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L855" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L855" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L855" data-line-number="855" class="file-line-num gl-select-none !gl-shadow-none">
        855
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L856" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L856" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L856" data-line-number="856" class="file-line-num gl-select-none !gl-shadow-none">
        856
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L857" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L857" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L857" data-line-number="857" class="file-line-num gl-select-none !gl-shadow-none">
        857
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L858" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L858" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L858" data-line-number="858" class="file-line-num gl-select-none !gl-shadow-none">
        858
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L859" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L859" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L859" data-line-number="859" class="file-line-num gl-select-none !gl-shadow-none">
        859
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L860" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L860" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L860" data-line-number="860" class="file-line-num gl-select-none !gl-shadow-none">
        860
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L861" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L861" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L861" data-line-number="861" class="file-line-num gl-select-none !gl-shadow-none">
        861
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L862" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L862" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L862" data-line-number="862" class="file-line-num gl-select-none !gl-shadow-none">
        862
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L863" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L863" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L863" data-line-number="863" class="file-line-num gl-select-none !gl-shadow-none">
        863
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L864" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L864" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L864" data-line-number="864" class="file-line-num gl-select-none !gl-shadow-none">
        864
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L865" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L865" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L865" data-line-number="865" class="file-line-num gl-select-none !gl-shadow-none">
        865
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L866" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L866" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L866" data-line-number="866" class="file-line-num gl-select-none !gl-shadow-none">
        866
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L867" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L867" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L867" data-line-number="867" class="file-line-num gl-select-none !gl-shadow-none">
        867
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L868" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L868" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L868" data-line-number="868" class="file-line-num gl-select-none !gl-shadow-none">
        868
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L869" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L869" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L869" data-line-number="869" class="file-line-num gl-select-none !gl-shadow-none">
        869
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L870" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L870" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L870" data-line-number="870" class="file-line-num gl-select-none !gl-shadow-none">
        870
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L871" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L871" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L871" data-line-number="871" class="file-line-num gl-select-none !gl-shadow-none">
        871
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L872" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L872" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L872" data-line-number="872" class="file-line-num gl-select-none !gl-shadow-none">
        872
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L873" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L873" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L873" data-line-number="873" class="file-line-num gl-select-none !gl-shadow-none">
        873
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L874" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L874" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L874" data-line-number="874" class="file-line-num gl-select-none !gl-shadow-none">
        874
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L875" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L875" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L875" data-line-number="875" class="file-line-num gl-select-none !gl-shadow-none">
        875
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L876" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L876" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L876" data-line-number="876" class="file-line-num gl-select-none !gl-shadow-none">
        876
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L877" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L877" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L877" data-line-number="877" class="file-line-num gl-select-none !gl-shadow-none">
        877
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L878" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L878" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L878" data-line-number="878" class="file-line-num gl-select-none !gl-shadow-none">
        878
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L879" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L879" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L879" data-line-number="879" class="file-line-num gl-select-none !gl-shadow-none">
        879
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L880" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L880" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L880" data-line-number="880" class="file-line-num gl-select-none !gl-shadow-none">
        880
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L881" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L881" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L881" data-line-number="881" class="file-line-num gl-select-none !gl-shadow-none">
        881
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L882" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L882" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L882" data-line-number="882" class="file-line-num gl-select-none !gl-shadow-none">
        882
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L883" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L883" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L883" data-line-number="883" class="file-line-num gl-select-none !gl-shadow-none">
        883
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L884" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L884" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L884" data-line-number="884" class="file-line-num gl-select-none !gl-shadow-none">
        884
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L885" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L885" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L885" data-line-number="885" class="file-line-num gl-select-none !gl-shadow-none">
        885
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L886" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L886" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L886" data-line-number="886" class="file-line-num gl-select-none !gl-shadow-none">
        886
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L887" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L887" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L887" data-line-number="887" class="file-line-num gl-select-none !gl-shadow-none">
        887
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L888" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L888" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L888" data-line-number="888" class="file-line-num gl-select-none !gl-shadow-none">
        888
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L889" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L889" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L889" data-line-number="889" class="file-line-num gl-select-none !gl-shadow-none">
        889
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L890" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L890" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L890" data-line-number="890" class="file-line-num gl-select-none !gl-shadow-none">
        890
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L891" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L891" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L891" data-line-number="891" class="file-line-num gl-select-none !gl-shadow-none">
        891
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L892" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L892" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L892" data-line-number="892" class="file-line-num gl-select-none !gl-shadow-none">
        892
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L893" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L893" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L893" data-line-number="893" class="file-line-num gl-select-none !gl-shadow-none">
        893
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L894" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L894" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L894" data-line-number="894" class="file-line-num gl-select-none !gl-shadow-none">
        894
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L895" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L895" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L895" data-line-number="895" class="file-line-num gl-select-none !gl-shadow-none">
        895
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L896" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L896" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L896" data-line-number="896" class="file-line-num gl-select-none !gl-shadow-none">
        896
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L897" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L897" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L897" data-line-number="897" class="file-line-num gl-select-none !gl-shadow-none">
        897
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L898" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L898" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L898" data-line-number="898" class="file-line-num gl-select-none !gl-shadow-none">
        898
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L899" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L899" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L899" data-line-number="899" class="file-line-num gl-select-none !gl-shadow-none">
        899
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L900" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L900" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L900" data-line-number="900" class="file-line-num gl-select-none !gl-shadow-none">
        900
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L901" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L901" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L901" data-line-number="901" class="file-line-num gl-select-none !gl-shadow-none">
        901
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L902" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L902" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L902" data-line-number="902" class="file-line-num gl-select-none !gl-shadow-none">
        902
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L903" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L903" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L903" data-line-number="903" class="file-line-num gl-select-none !gl-shadow-none">
        903
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L904" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L904" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L904" data-line-number="904" class="file-line-num gl-select-none !gl-shadow-none">
        904
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L905" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L905" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L905" data-line-number="905" class="file-line-num gl-select-none !gl-shadow-none">
        905
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L906" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L906" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L906" data-line-number="906" class="file-line-num gl-select-none !gl-shadow-none">
        906
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L907" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L907" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L907" data-line-number="907" class="file-line-num gl-select-none !gl-shadow-none">
        907
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L908" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L908" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L908" data-line-number="908" class="file-line-num gl-select-none !gl-shadow-none">
        908
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L909" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L909" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L909" data-line-number="909" class="file-line-num gl-select-none !gl-shadow-none">
        909
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L910" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L910" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L910" data-line-number="910" class="file-line-num gl-select-none !gl-shadow-none">
        910
      </a></div></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" style="margin-left: 96px;"><div class="line" lang="c" id="LC841"></div>
<div class="line" lang="c" id="LC842"><span class="">	</span><span class="hljs-keyword">do</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC843"><span class="">		c </span><span class="">= zmodem_rx</span><span class="">(zm)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC844"></div>
<div class="line" lang="c" id="LC845"><span class="">		</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(c &lt; </span><span class="hljs-number">0</span><span class="">)</span></div>
<div class="line" lang="c" id="LC846"><span class="">			</span><span class="hljs-keyword">return</span><span class=""> c;</span></div>
<div class="line" lang="c" id="LC847"></div>
<div class="line" lang="c" id="LC848"><span class="">		</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(c &gt; </span><span class="hljs-number">0xff</span><span class="">)</span></div>
<div class="line" lang="c" id="LC849"><span class="">			</span><span class="hljs-keyword">break</span><span class="">;</span></div>
<div class="line" lang="c" id="LC850"></div>
<div class="line" lang="c" id="LC851"><span class="">		</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(*len &gt;= maxlen)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC852"><span class="">			lprintf</span><span class="">(zm, LOG_ERR, </span><span class="hljs-string">"%lu Subpacket OVERFLOW (%u &gt;= %u)"</span><span class="">, </span><span class="">(ulong)</span><span class="">zm-&gt;ack_file_pos, *len, maxlen)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC853"><span class="">			</span><span class="hljs-keyword">return</span><span class=""> SUBPKTOVERFLOW;</span></div>
<div class="line" lang="c" id="LC854"><span class="">		}</span></div>
<div class="line" lang="c" id="LC855"><span class="">		crc </span><span class="">= ucrc32</span><span class="">(c, crc)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC856"><span class="">		*p++ </span><span class="">= c;</span></div>
<div class="line" lang="c" id="LC857"><span class="">		</span><span class="">(*len)</span><span class="">++;</span></div>
<div class="line" lang="c" id="LC858"><span class="">	} </span><span class="hljs-keyword">while</span><span class=""> </span><span class="">(</span><span class="hljs-number">1</span><span class="">)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC859"></div>
<div class="line" lang="c" id="LC860"><span class="">	subpkt_type </span><span class="">= c &amp; </span><span class="hljs-number">0xff</span><span class="">;</span></div>
<div class="line" lang="c" id="LC861"><span class="">	*type </span><span class="">= subpkt_type;</span></div>
<div class="line" lang="c" id="LC862"></div>
<div class="line" lang="c" id="LC863"><span class="">	crc </span><span class="">= ucrc32</span><span class="">(subpkt_type, crc)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC864"></div>
<div class="line" lang="c" id="LC865"><span class="">	crc </span><span class="">= ~crc;</span></div>
<div class="line" lang="c" id="LC866"></div>
<div class="line" lang="c" id="LC867"><span class="">	rxd_crc  </span><span class="">= zmodem_rx</span><span class="">(zm)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC868"><span class="">	rxd_crc |</span><span class="">= zmodem_rx</span><span class="">(zm)</span><span class=""> &lt;&lt; </span><span class="hljs-number">8</span><span class="">;</span></div>
<div class="line" lang="c" id="LC869"><span class="">	rxd_crc |</span><span class="">= zmodem_rx</span><span class="">(zm)</span><span class=""> &lt;&lt; </span><span class="hljs-number">16</span><span class="">;</span></div>
<div class="line" lang="c" id="LC870"><span class="">	rxd_crc |</span><span class="">= zmodem_rx</span><span class="">(zm)</span><span class=""> &lt;&lt; </span><span class="hljs-number">24</span><span class="">;</span></div>
<div class="line" lang="c" id="LC871"></div>
<div class="line" lang="c" id="LC872"><span class="">	</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(rxd_crc != crc)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC873"><span class="">		lprintf</span><span class="">(zm, LOG_DEBUG, </span><span class="hljs-string">"%lu %s CRC ERROR (%08X, expected: %08X) Bytes=%u, subpacket type=%s"</span></div>
<div class="line" lang="c" id="LC874"><span class="">		        , </span><span class="">(ulong)</span><span class="">zm-&gt;ack_file_pos, __FUNCTION__, rxd_crc, crc, *len, chr</span><span class="">(subpkt_type)</span><span class="">)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC875"><span class="">		</span><span class="hljs-keyword">return</span><span class=""> CRCFAILED;</span></div>
<div class="line" lang="c" id="LC876"><span class="">	}</span></div>
<div class="line" lang="c" id="LC877"><span class="hljs-comment">//	lprintf(zm,LOG_DEBUG, "%lu %s GOOD CRC: %08lX (Bytes=%u, subpacket type=%s)"</span></div>
<div class="line" lang="c" id="LC878"><span class="hljs-comment">//		,(ulong)zm-&gt;ack_file_pos, __FUNCTION__, crc, *len, chr(subpkt_type));</span></div>
<div class="line" lang="c" id="LC879"></div>
<div class="line" lang="c" id="LC880"><span class="">	zm-&gt;ack_file_pos +</span><span class="">= *len;</span></div>
<div class="line" lang="c" id="LC881"></div>
<div class="line" lang="c" id="LC882"><span class="">	</span><span class="hljs-keyword">return</span><span class=""> subpkt_type;</span></div>
<div class="line" lang="c" id="LC883"><span class="">}</span></div>
<div class="line" lang="c" id="LC884"></div>
<div class="line" lang="c" id="LC885"><span class="hljs-type">int</span><span class=""> </span><span class="hljs-title.function">zmodem_recv_data16</span><span class="hljs-params"><span class="hljs-params">(</span><span class="hljs-type">zmodem_t</span><span class="hljs-params">* zm, </span><span class="hljs-keyword">register</span><span class="hljs-params"> </span><span class="hljs-type">unsigned</span><span class="hljs-params"> </span><span class="hljs-type">char</span><span class="hljs-params">* p, </span><span class="hljs-type">unsigned</span><span class="hljs-params"> maxlen, </span><span class="hljs-type">unsigned</span><span class="hljs-params">* len, </span><span class="hljs-type">int</span><span class="hljs-params">* type)</span></span></div>
<div class="line" lang="c" id="LC886"><span class="">{</span></div>
<div class="line" lang="c" id="LC887"><span class="">	</span><span class="hljs-type">int</span><span class="">            c;</span></div>
<div class="line" lang="c" id="LC888"><span class="">	</span><span class="hljs-type">int</span><span class="">            subpkt_type;</span></div>
<div class="line" lang="c" id="LC889"><span class="">	</span><span class="hljs-type">unsigned</span><span class=""> </span><span class="hljs-type">short</span><span class=""> crc;</span></div>
<div class="line" lang="c" id="LC890"><span class="">	</span><span class="hljs-type">unsigned</span><span class=""> </span><span class="hljs-type">short</span><span class=""> rxd_crc;</span></div>
<div class="line" lang="c" id="LC891"></div>
<div class="line" lang="c" id="LC892"><span class="hljs-comment">//	lprintf(zm, LOG_DEBUG, __FUNCTION__);</span></div>
<div class="line" lang="c" id="LC893"></div>
<div class="line" lang="c" id="LC894"><span class="">	crc </span><span class="">= </span><span class="hljs-number">0</span><span class="">;</span></div>
<div class="line" lang="c" id="LC895"><span class="">	*type </span><span class="">= INVALIDSUBPKT;</span></div>
<div class="line" lang="c" id="LC896"></div>
<div class="line" lang="c" id="LC897"><span class="">	</span><span class="hljs-keyword">do</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC898"><span class="">		c </span><span class="">= zmodem_rx</span><span class="">(zm)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC899"></div>
<div class="line" lang="c" id="LC900"><span class="">		</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(c &lt; </span><span class="hljs-number">0</span><span class="">)</span></div>
<div class="line" lang="c" id="LC901"><span class="">			</span><span class="hljs-keyword">return</span><span class=""> c;</span></div>
<div class="line" lang="c" id="LC902"></div>
<div class="line" lang="c" id="LC903"><span class="">		</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(c &gt; </span><span class="hljs-number">0xff</span><span class="">)</span></div>
<div class="line" lang="c" id="LC904"><span class="">			</span><span class="hljs-keyword">break</span><span class="">;</span></div>
<div class="line" lang="c" id="LC905"></div>
<div class="line" lang="c" id="LC906"><span class="">		</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(*len &gt;= maxlen)</span></div>
<div class="line" lang="c" id="LC907"><span class="">			</span><span class="hljs-keyword">return</span><span class=""> SUBPKTOVERFLOW;</span></div>
<div class="line" lang="c" id="LC908"><span class="">		crc </span><span class="">= ucrc16</span><span class="">(c, crc)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC909"><span class="">		*p++ </span><span class="">= c;</span></div>
<div class="line" lang="c" id="LC910"><span class="">		</span><span class="">(*len)</span><span class="">++;</span></div></code></pre></div></div><div class="gl-flex"><div class="gl-absolute gl-flex gl-flex-col"><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L911" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L911" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L911" data-line-number="911" class="file-line-num gl-select-none !gl-shadow-none">
        911
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L912" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L912" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L912" data-line-number="912" class="file-line-num gl-select-none !gl-shadow-none">
        912
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L913" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L913" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L913" data-line-number="913" class="file-line-num gl-select-none !gl-shadow-none">
        913
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L914" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L914" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L914" data-line-number="914" class="file-line-num gl-select-none !gl-shadow-none">
        914
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L915" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L915" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L915" data-line-number="915" class="file-line-num gl-select-none !gl-shadow-none">
        915
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L916" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L916" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L916" data-line-number="916" class="file-line-num gl-select-none !gl-shadow-none">
        916
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L917" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L917" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L917" data-line-number="917" class="file-line-num gl-select-none !gl-shadow-none">
        917
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L918" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L918" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L918" data-line-number="918" class="file-line-num gl-select-none !gl-shadow-none">
        918
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L919" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L919" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L919" data-line-number="919" class="file-line-num gl-select-none !gl-shadow-none">
        919
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L920" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L920" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L920" data-line-number="920" class="file-line-num gl-select-none !gl-shadow-none">
        920
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L921" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L921" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L921" data-line-number="921" class="file-line-num gl-select-none !gl-shadow-none">
        921
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L922" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L922" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L922" data-line-number="922" class="file-line-num gl-select-none !gl-shadow-none">
        922
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L923" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L923" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L923" data-line-number="923" class="file-line-num gl-select-none !gl-shadow-none">
        923
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L924" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L924" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L924" data-line-number="924" class="file-line-num gl-select-none !gl-shadow-none">
        924
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L925" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L925" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L925" data-line-number="925" class="file-line-num gl-select-none !gl-shadow-none">
        925
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L926" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L926" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L926" data-line-number="926" class="file-line-num gl-select-none !gl-shadow-none">
        926
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L927" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L927" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L927" data-line-number="927" class="file-line-num gl-select-none !gl-shadow-none">
        927
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L928" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L928" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L928" data-line-number="928" class="file-line-num gl-select-none !gl-shadow-none">
        928
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L929" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L929" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L929" data-line-number="929" class="file-line-num gl-select-none !gl-shadow-none">
        929
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L930" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L930" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L930" data-line-number="930" class="file-line-num gl-select-none !gl-shadow-none">
        930
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L931" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L931" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L931" data-line-number="931" class="file-line-num gl-select-none !gl-shadow-none">
        931
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L932" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L932" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L932" data-line-number="932" class="file-line-num gl-select-none !gl-shadow-none">
        932
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L933" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L933" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L933" data-line-number="933" class="file-line-num gl-select-none !gl-shadow-none">
        933
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L934" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L934" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L934" data-line-number="934" class="file-line-num gl-select-none !gl-shadow-none">
        934
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L935" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L935" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L935" data-line-number="935" class="file-line-num gl-select-none !gl-shadow-none">
        935
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L936" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L936" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L936" data-line-number="936" class="file-line-num gl-select-none !gl-shadow-none">
        936
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L937" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L937" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L937" data-line-number="937" class="file-line-num gl-select-none !gl-shadow-none">
        937
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L938" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L938" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L938" data-line-number="938" class="file-line-num gl-select-none !gl-shadow-none">
        938
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L939" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L939" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L939" data-line-number="939" class="file-line-num gl-select-none !gl-shadow-none">
        939
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L940" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L940" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L940" data-line-number="940" class="file-line-num gl-select-none !gl-shadow-none">
        940
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L941" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L941" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L941" data-line-number="941" class="file-line-num gl-select-none !gl-shadow-none">
        941
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L942" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L942" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L942" data-line-number="942" class="file-line-num gl-select-none !gl-shadow-none">
        942
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L943" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L943" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L943" data-line-number="943" class="file-line-num gl-select-none !gl-shadow-none">
        943
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L944" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L944" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L944" data-line-number="944" class="file-line-num gl-select-none !gl-shadow-none">
        944
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L945" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L945" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L945" data-line-number="945" class="file-line-num gl-select-none !gl-shadow-none">
        945
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L946" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L946" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L946" data-line-number="946" class="file-line-num gl-select-none !gl-shadow-none">
        946
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L947" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L947" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L947" data-line-number="947" class="file-line-num gl-select-none !gl-shadow-none">
        947
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L948" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L948" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L948" data-line-number="948" class="file-line-num gl-select-none !gl-shadow-none">
        948
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L949" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L949" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L949" data-line-number="949" class="file-line-num gl-select-none !gl-shadow-none">
        949
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L950" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L950" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L950" data-line-number="950" class="file-line-num gl-select-none !gl-shadow-none">
        950
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L951" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L951" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L951" data-line-number="951" class="file-line-num gl-select-none !gl-shadow-none">
        951
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L952" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L952" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L952" data-line-number="952" class="file-line-num gl-select-none !gl-shadow-none">
        952
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L953" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L953" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L953" data-line-number="953" class="file-line-num gl-select-none !gl-shadow-none">
        953
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L954" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L954" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L954" data-line-number="954" class="file-line-num gl-select-none !gl-shadow-none">
        954
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L955" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L955" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L955" data-line-number="955" class="file-line-num gl-select-none !gl-shadow-none">
        955
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L956" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L956" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L956" data-line-number="956" class="file-line-num gl-select-none !gl-shadow-none">
        956
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L957" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L957" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L957" data-line-number="957" class="file-line-num gl-select-none !gl-shadow-none">
        957
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L958" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L958" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L958" data-line-number="958" class="file-line-num gl-select-none !gl-shadow-none">
        958
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L959" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L959" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L959" data-line-number="959" class="file-line-num gl-select-none !gl-shadow-none">
        959
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L960" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L960" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L960" data-line-number="960" class="file-line-num gl-select-none !gl-shadow-none">
        960
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L961" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L961" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L961" data-line-number="961" class="file-line-num gl-select-none !gl-shadow-none">
        961
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L962" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L962" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L962" data-line-number="962" class="file-line-num gl-select-none !gl-shadow-none">
        962
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L963" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L963" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L963" data-line-number="963" class="file-line-num gl-select-none !gl-shadow-none">
        963
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L964" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L964" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L964" data-line-number="964" class="file-line-num gl-select-none !gl-shadow-none">
        964
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L965" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L965" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L965" data-line-number="965" class="file-line-num gl-select-none !gl-shadow-none">
        965
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L966" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L966" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L966" data-line-number="966" class="file-line-num gl-select-none !gl-shadow-none">
        966
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L967" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L967" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L967" data-line-number="967" class="file-line-num gl-select-none !gl-shadow-none">
        967
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L968" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L968" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L968" data-line-number="968" class="file-line-num gl-select-none !gl-shadow-none">
        968
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L969" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L969" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L969" data-line-number="969" class="file-line-num gl-select-none !gl-shadow-none">
        969
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L970" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L970" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L970" data-line-number="970" class="file-line-num gl-select-none !gl-shadow-none">
        970
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L971" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L971" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L971" data-line-number="971" class="file-line-num gl-select-none !gl-shadow-none">
        971
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L972" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L972" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L972" data-line-number="972" class="file-line-num gl-select-none !gl-shadow-none">
        972
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L973" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L973" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L973" data-line-number="973" class="file-line-num gl-select-none !gl-shadow-none">
        973
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L974" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L974" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L974" data-line-number="974" class="file-line-num gl-select-none !gl-shadow-none">
        974
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L975" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L975" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L975" data-line-number="975" class="file-line-num gl-select-none !gl-shadow-none">
        975
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L976" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L976" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L976" data-line-number="976" class="file-line-num gl-select-none !gl-shadow-none">
        976
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L977" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L977" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L977" data-line-number="977" class="file-line-num gl-select-none !gl-shadow-none">
        977
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L978" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L978" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L978" data-line-number="978" class="file-line-num gl-select-none !gl-shadow-none">
        978
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L979" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L979" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L979" data-line-number="979" class="file-line-num gl-select-none !gl-shadow-none">
        979
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L980" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L980" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L980" data-line-number="980" class="file-line-num gl-select-none !gl-shadow-none">
        980
      </a></div></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" style="margin-left: 96px;"><div class="line" lang="c" id="LC911"><span class="">	} </span><span class="hljs-keyword">while</span><span class=""> </span><span class="">(</span><span class="hljs-number">1</span><span class="">)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC912"></div>
<div class="line" lang="c" id="LC913"><span class="">	subpkt_type </span><span class="">= c &amp; </span><span class="hljs-number">0xff</span><span class="">;</span></div>
<div class="line" lang="c" id="LC914"><span class="">	*type </span><span class="">= subpkt_type;</span></div>
<div class="line" lang="c" id="LC915"></div>
<div class="line" lang="c" id="LC916"><span class="">	crc </span><span class="">= ucrc16</span><span class="">(subpkt_type, crc)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC917"></div>
<div class="line" lang="c" id="LC918"><span class="">	c </span><span class="">= zmodem_rx</span><span class="">(zm)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC919"><span class="">	</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(c &lt; </span><span class="hljs-number">0</span><span class="">)</span></div>
<div class="line" lang="c" id="LC920"><span class="">		</span><span class="hljs-keyword">return</span><span class=""> c;</span></div>
<div class="line" lang="c" id="LC921"><span class="">	rxd_crc  </span><span class="">= c &lt;&lt; </span><span class="hljs-number">8</span><span class="">;</span></div>
<div class="line" lang="c" id="LC922"><span class="">	c </span><span class="">= zmodem_rx</span><span class="">(zm)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC923"><span class="">	</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(c &lt; </span><span class="hljs-number">0</span><span class="">)</span></div>
<div class="line" lang="c" id="LC924"><span class="">		</span><span class="hljs-keyword">return</span><span class=""> c;</span></div>
<div class="line" lang="c" id="LC925"><span class="">	rxd_crc |</span><span class="">= c;</span></div>
<div class="line" lang="c" id="LC926"></div>
<div class="line" lang="c" id="LC927"><span class="">	</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(rxd_crc != crc)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC928"><span class="">		lprintf</span><span class="">(zm, LOG_DEBUG, </span><span class="hljs-string">"%lu %s CRC ERROR (%04hX, expected: %04hX) Bytes=%u, subpacket type=%s"</span></div>
<div class="line" lang="c" id="LC929"><span class="">		        , </span><span class="">(ulong)</span><span class="">zm-&gt;ack_file_pos, __FUNCTION__, rxd_crc, crc, *len, chr</span><span class="">(subpkt_type)</span><span class="">)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC930"><span class="">		</span><span class="hljs-keyword">return</span><span class=""> CRCFAILED;</span></div>
<div class="line" lang="c" id="LC931"><span class="">	}</span></div>
<div class="line" lang="c" id="LC932"><span class="hljs-comment">//	lprintf(zm,LOG_DEBUG, "%lu %s GOOD CRC: %04hX (Bytes=%d, subpacket type=%s)"</span></div>
<div class="line" lang="c" id="LC933"><span class="hljs-comment">//		,(ulong)zm-&gt;ack_file_pos, __FUNCTION__, crc, *len, chr(subpkt_type));</span></div>
<div class="line" lang="c" id="LC934"></div>
<div class="line" lang="c" id="LC935"><span class="">	zm-&gt;ack_file_pos +</span><span class="">= *len;</span></div>
<div class="line" lang="c" id="LC936"></div>
<div class="line" lang="c" id="LC937"><span class="">	</span><span class="hljs-keyword">return</span><span class=""> subpkt_type;</span></div>
<div class="line" lang="c" id="LC938"><span class="">}</span></div>
<div class="line" lang="c" id="LC939"></div>
<div class="line" lang="c" id="LC940"><span class="hljs-type">int</span><span class=""> </span><span class="hljs-title.function">zmodem_recv_data</span><span class="hljs-params"><span class="hljs-params">(</span><span class="hljs-type">zmodem_t</span><span class="hljs-params">* zm, </span><span class="hljs-type">unsigned</span><span class="hljs-params"> </span><span class="hljs-type">char</span><span class="hljs-params">* buf, </span><span class="hljs-type">size_t</span><span class="hljs-params"> maxlen, </span><span class="hljs-type">unsigned</span><span class="hljs-params">* len, BOOL ack, </span><span class="hljs-type">int</span><span class="hljs-params">* type)</span></span></div>
<div class="line" lang="c" id="LC941"><span class="">{</span></div>
<div class="line" lang="c" id="LC942"><span class="">	</span><span class="hljs-type">int</span><span class="">      subpkt_type;</span></div>
<div class="line" lang="c" id="LC943"><span class="">	</span><span class="hljs-type">unsigned</span><span class=""> n </span><span class="">= </span><span class="hljs-number">0</span><span class="">;</span></div>
<div class="line" lang="c" id="LC944"></div>
<div class="line" lang="c" id="LC945"><span class="">	</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(len == </span><span class="hljs-literal">NULL</span><span class="">)</span></div>
<div class="line" lang="c" id="LC946"><span class="">		len </span><span class="">= &amp;n;</span></div>
<div class="line" lang="c" id="LC947"></div>
<div class="line" lang="c" id="LC948"><span class="hljs-comment">//	lprintf(zm,LOG_DEBUG, __FUNCTION__ " (%u-bit)", zm-&gt;receive_32bit_data ? 32:16);</span></div>
<div class="line" lang="c" id="LC949"></div>
<div class="line" lang="c" id="LC950"><span class="">	</span><span class="hljs-comment"><span class="hljs-comment">/*</span></span></div>
<div class="line" lang="c" id="LC951"><span class="hljs-comment">	 *</span><span class="hljs-comment"> receive the right </span><span class="hljs-comment">type of frame</span></div>
<div class="line" lang="c" id="LC952"><span class="hljs-comment">	 */</span></div>
<div class="line" lang="c" id="LC953"></div>
<div class="line" lang="c" id="LC954"><span class="">	*len </span><span class="">= </span><span class="hljs-number">0</span><span class="">;</span></div>
<div class="line" lang="c" id="LC955"></div>
<div class="line" lang="c" id="LC956"><span class="">	</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(zm-&gt;receive_32bit_data)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC957"><span class="">		subpkt_type </span><span class="">= zmodem_recv_data32</span><span class="">(zm, buf, maxlen, len, type)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC958"><span class="">	}</span></div>
<div class="line" lang="c" id="LC959"><span class="">	</span><span class="hljs-keyword">else</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC960"><span class="">		subpkt_type = zmodem_recv_data16</span><span class="">(zm, buf, maxlen, len, type)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC961"><span class="">	}</span></div>
<div class="line" lang="c" id="LC962"></div>
<div class="line" lang="c" id="LC963"><span class="">	</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(subpkt_type &lt;= </span><span class="hljs-number">0</span><span class="">)</span><span class=""> {  </span><span class="hljs-comment">/* e.g. TIMEOUT, SUBPKTOVERFLOW, CRCFAILED */</span></div>
<div class="line" lang="c" id="LC964"><span class="">		lprintf</span><span class="">(zm, LOG_WARNING, </span><span class="hljs-string">"%s data subpacket (%u bytes) %s"</span></div>
<div class="line" lang="c" id="LC965"><span class="">		        , chr</span><span class="">(*type)</span><span class="">, *len, chr</span><span class="">(subpkt_type)</span><span class="">)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC966"><span class="">		</span><span class="hljs-keyword">return</span><span class=""> subpkt_type;</span></div>
<div class="line" lang="c" id="LC967"><span class="">	}</span></div>
<div class="line" lang="c" id="LC968"></div>
<div class="line" lang="c" id="LC969"><span class="">	lprintf</span><span class="">(zm, LOG_DEBUG, </span><span class="hljs-string">"%lu Successful receipt of subpacket type: %s (%u bytes)"</span></div>
<div class="line" lang="c" id="LC970"><span class="">	        , </span><span class="">(ulong)</span><span class="">zm-&gt;ack_file_pos, chr</span><span class="">(subpkt_type)</span><span class="">, *len)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC971"></div>
<div class="line" lang="c" id="LC972"><span class="">	</span><span class="hljs-keyword">switch</span><span class=""> </span><span class="">(subpkt_type)</span><span class="">  {</span></div>
<div class="line" lang="c" id="LC973"><span class="">		</span><span class="hljs-comment">/*</span></div>
<div class="line" lang="c" id="LC974"><span class="hljs-comment">		 * frame continues non-stop</span></div>
<div class="line" lang="c" id="LC975"><span class="hljs-comment">		 */</span></div>
<div class="line" lang="c" id="LC976"><span class="">		</span><span class="hljs-keyword">case</span><span class=""> ZCRCG:</span></div>
<div class="line" lang="c" id="LC977"><span class="">			</span><span class="hljs-keyword">return</span><span class=""> FRAMEOK;</span></div>
<div class="line" lang="c" id="LC978"><span class="">		</span><span class="hljs-comment">/*</span></div>
<div class="line" lang="c" id="LC979"><span class="hljs-comment">		 * frame ends</span></div>
<div class="line" lang="c" id="LC980"><span class="hljs-comment">		 */</span></div></code></pre></div></div><div class="gl-flex"><div class="gl-absolute gl-flex gl-flex-col"><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L981" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L981" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L981" data-line-number="981" class="file-line-num gl-select-none !gl-shadow-none">
        981
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L982" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L982" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L982" data-line-number="982" class="file-line-num gl-select-none !gl-shadow-none">
        982
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L983" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L983" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L983" data-line-number="983" class="file-line-num gl-select-none !gl-shadow-none">
        983
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L984" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L984" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L984" data-line-number="984" class="file-line-num gl-select-none !gl-shadow-none">
        984
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L985" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L985" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L985" data-line-number="985" class="file-line-num gl-select-none !gl-shadow-none">
        985
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L986" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L986" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L986" data-line-number="986" class="file-line-num gl-select-none !gl-shadow-none">
        986
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L987" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L987" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L987" data-line-number="987" class="file-line-num gl-select-none !gl-shadow-none">
        987
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L988" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L988" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L988" data-line-number="988" class="file-line-num gl-select-none !gl-shadow-none">
        988
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L989" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L989" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L989" data-line-number="989" class="file-line-num gl-select-none !gl-shadow-none">
        989
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L990" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L990" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L990" data-line-number="990" class="file-line-num gl-select-none !gl-shadow-none">
        990
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L991" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L991" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L991" data-line-number="991" class="file-line-num gl-select-none !gl-shadow-none">
        991
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L992" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L992" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L992" data-line-number="992" class="file-line-num gl-select-none !gl-shadow-none">
        992
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L993" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L993" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L993" data-line-number="993" class="file-line-num gl-select-none !gl-shadow-none">
        993
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L994" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L994" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L994" data-line-number="994" class="file-line-num gl-select-none !gl-shadow-none">
        994
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L995" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L995" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L995" data-line-number="995" class="file-line-num gl-select-none !gl-shadow-none">
        995
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L996" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L996" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L996" data-line-number="996" class="file-line-num gl-select-none !gl-shadow-none">
        996
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L997" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L997" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L997" data-line-number="997" class="file-line-num gl-select-none !gl-shadow-none">
        997
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L998" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L998" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L998" data-line-number="998" class="file-line-num gl-select-none !gl-shadow-none">
        998
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L999" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L999" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L999" data-line-number="999" class="file-line-num gl-select-none !gl-shadow-none">
        999
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1000" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1000" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1000" data-line-number="1000" class="file-line-num gl-select-none !gl-shadow-none">
        1000
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1001" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1001" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1001" data-line-number="1001" class="file-line-num gl-select-none !gl-shadow-none">
        1001
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1002" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1002" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1002" data-line-number="1002" class="file-line-num gl-select-none !gl-shadow-none">
        1002
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1003" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1003" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1003" data-line-number="1003" class="file-line-num gl-select-none !gl-shadow-none">
        1003
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1004" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1004" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1004" data-line-number="1004" class="file-line-num gl-select-none !gl-shadow-none">
        1004
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1005" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1005" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1005" data-line-number="1005" class="file-line-num gl-select-none !gl-shadow-none">
        1005
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1006" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1006" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1006" data-line-number="1006" class="file-line-num gl-select-none !gl-shadow-none">
        1006
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1007" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1007" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1007" data-line-number="1007" class="file-line-num gl-select-none !gl-shadow-none">
        1007
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1008" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1008" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1008" data-line-number="1008" class="file-line-num gl-select-none !gl-shadow-none">
        1008
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1009" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1009" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1009" data-line-number="1009" class="file-line-num gl-select-none !gl-shadow-none">
        1009
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1010" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1010" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1010" data-line-number="1010" class="file-line-num gl-select-none !gl-shadow-none">
        1010
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1011" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1011" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1011" data-line-number="1011" class="file-line-num gl-select-none !gl-shadow-none">
        1011
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1012" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1012" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1012" data-line-number="1012" class="file-line-num gl-select-none !gl-shadow-none">
        1012
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1013" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1013" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1013" data-line-number="1013" class="file-line-num gl-select-none !gl-shadow-none">
        1013
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1014" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1014" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1014" data-line-number="1014" class="file-line-num gl-select-none !gl-shadow-none">
        1014
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1015" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1015" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1015" data-line-number="1015" class="file-line-num gl-select-none !gl-shadow-none">
        1015
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1016" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1016" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1016" data-line-number="1016" class="file-line-num gl-select-none !gl-shadow-none">
        1016
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1017" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1017" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1017" data-line-number="1017" class="file-line-num gl-select-none !gl-shadow-none">
        1017
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1018" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1018" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1018" data-line-number="1018" class="file-line-num gl-select-none !gl-shadow-none">
        1018
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1019" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1019" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1019" data-line-number="1019" class="file-line-num gl-select-none !gl-shadow-none">
        1019
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1020" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1020" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1020" data-line-number="1020" class="file-line-num gl-select-none !gl-shadow-none">
        1020
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1021" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1021" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1021" data-line-number="1021" class="file-line-num gl-select-none !gl-shadow-none">
        1021
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1022" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1022" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1022" data-line-number="1022" class="file-line-num gl-select-none !gl-shadow-none">
        1022
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1023" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1023" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1023" data-line-number="1023" class="file-line-num gl-select-none !gl-shadow-none">
        1023
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1024" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1024" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1024" data-line-number="1024" class="file-line-num gl-select-none !gl-shadow-none">
        1024
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1025" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1025" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1025" data-line-number="1025" class="file-line-num gl-select-none !gl-shadow-none">
        1025
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1026" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1026" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1026" data-line-number="1026" class="file-line-num gl-select-none !gl-shadow-none">
        1026
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1027" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1027" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1027" data-line-number="1027" class="file-line-num gl-select-none !gl-shadow-none">
        1027
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1028" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1028" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1028" data-line-number="1028" class="file-line-num gl-select-none !gl-shadow-none">
        1028
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1029" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1029" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1029" data-line-number="1029" class="file-line-num gl-select-none !gl-shadow-none">
        1029
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1030" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1030" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1030" data-line-number="1030" class="file-line-num gl-select-none !gl-shadow-none">
        1030
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1031" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1031" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1031" data-line-number="1031" class="file-line-num gl-select-none !gl-shadow-none">
        1031
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1032" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1032" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1032" data-line-number="1032" class="file-line-num gl-select-none !gl-shadow-none">
        1032
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1033" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1033" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1033" data-line-number="1033" class="file-line-num gl-select-none !gl-shadow-none">
        1033
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1034" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1034" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1034" data-line-number="1034" class="file-line-num gl-select-none !gl-shadow-none">
        1034
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1035" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1035" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1035" data-line-number="1035" class="file-line-num gl-select-none !gl-shadow-none">
        1035
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1036" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1036" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1036" data-line-number="1036" class="file-line-num gl-select-none !gl-shadow-none">
        1036
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1037" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1037" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1037" data-line-number="1037" class="file-line-num gl-select-none !gl-shadow-none">
        1037
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1038" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1038" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1038" data-line-number="1038" class="file-line-num gl-select-none !gl-shadow-none">
        1038
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1039" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1039" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1039" data-line-number="1039" class="file-line-num gl-select-none !gl-shadow-none">
        1039
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1040" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1040" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1040" data-line-number="1040" class="file-line-num gl-select-none !gl-shadow-none">
        1040
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1041" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1041" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1041" data-line-number="1041" class="file-line-num gl-select-none !gl-shadow-none">
        1041
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1042" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1042" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1042" data-line-number="1042" class="file-line-num gl-select-none !gl-shadow-none">
        1042
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1043" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1043" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1043" data-line-number="1043" class="file-line-num gl-select-none !gl-shadow-none">
        1043
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1044" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1044" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1044" data-line-number="1044" class="file-line-num gl-select-none !gl-shadow-none">
        1044
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1045" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1045" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1045" data-line-number="1045" class="file-line-num gl-select-none !gl-shadow-none">
        1045
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1046" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1046" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1046" data-line-number="1046" class="file-line-num gl-select-none !gl-shadow-none">
        1046
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1047" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1047" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1047" data-line-number="1047" class="file-line-num gl-select-none !gl-shadow-none">
        1047
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1048" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1048" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1048" data-line-number="1048" class="file-line-num gl-select-none !gl-shadow-none">
        1048
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1049" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1049" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1049" data-line-number="1049" class="file-line-num gl-select-none !gl-shadow-none">
        1049
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1050" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1050" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1050" data-line-number="1050" class="file-line-num gl-select-none !gl-shadow-none">
        1050
      </a></div></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" style="margin-left: 96px;"><div class="line" lang="c" id="LC981"><span class="">		</span><span class="hljs-keyword">case</span><span class=""> ZCRCE:</span></div>
<div class="line" lang="c" id="LC982"><span class="">			</span><span class="hljs-keyword">return</span><span class=""> ENDOFFRAME;</span></div>
<div class="line" lang="c" id="LC983"><span class="">		</span><span class="hljs-comment">/*</span></div>
<div class="line" lang="c" id="LC984"><span class="hljs-comment">		 * frame continues; ZACK expected</span></div>
<div class="line" lang="c" id="LC985"><span class="hljs-comment">		 */</span></div>
<div class="line" lang="c" id="LC986"><span class="">		</span><span class="hljs-keyword">case</span><span class=""> ZCRCQ:</span></div>
<div class="line" lang="c" id="LC987"><span class="">			</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(ack)</span></div>
<div class="line" lang="c" id="LC988"><span class="">				zmodem_send_ack</span><span class="">(zm, zm-&gt;ack_file_pos)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC989"><span class="">			</span><span class="hljs-keyword">return</span><span class=""> FRAMEOK;</span></div>
<div class="line" lang="c" id="LC990"><span class="">		</span><span class="hljs-comment">/*</span></div>
<div class="line" lang="c" id="LC991"><span class="hljs-comment">		 * frame ends; ZACK expected</span></div>
<div class="line" lang="c" id="LC992"><span class="hljs-comment">		 */</span></div>
<div class="line" lang="c" id="LC993"><span class="">		</span><span class="hljs-keyword">case</span><span class=""> ZCRCW:</span></div>
<div class="line" lang="c" id="LC994"><span class="">			</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(ack)</span></div>
<div class="line" lang="c" id="LC995"><span class="">				zmodem_send_ack</span><span class="">(zm, zm-&gt;ack_file_pos)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC996"><span class="">			</span><span class="hljs-keyword">return</span><span class=""> ENDOFFRAME;</span></div>
<div class="line" lang="c" id="LC997"><span class="">	}</span></div>
<div class="line" lang="c" id="LC998"></div>
<div class="line" lang="c" id="LC999"><span class="">	lprintf</span><span class="">(zm, LOG_WARNING, </span><span class="hljs-string">"%lu INVALID subpacket type: %s (%u bytes)"</span></div>
<div class="line" lang="c" id="LC1000"><span class="">	        , </span><span class="">(ulong)</span><span class="">zm-&gt;ack_file_pos, chr</span><span class="">(subpkt_type)</span><span class="">, *len)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC1001"></div>
<div class="line" lang="c" id="LC1002"><span class="">	</span><span class="hljs-keyword">return</span><span class=""> INVALIDSUBPKT;</span></div>
<div class="line" lang="c" id="LC1003"><span class="">}</span></div>
<div class="line" lang="c" id="LC1004"></div>
<div class="line" lang="c" id="LC1005"><span class="">BOOL </span><span class="hljs-title.function">zmodem_recv_subpacket</span><span class="hljs-params"><span class="hljs-params">(</span><span class="hljs-type">zmodem_t</span><span class="hljs-params">* zm, BOOL ack, </span><span class="hljs-type">int</span><span class="hljs-params">* type)</span></span></div>
<div class="line" lang="c" id="LC1006"><span class="">{</span></div>
<div class="line" lang="c" id="LC1007"><span class="">	</span><span class="hljs-type">int</span><span class="">      result;</span></div>
<div class="line" lang="c" id="LC1008"><span class="">	</span><span class="hljs-type">unsigned</span><span class=""> len </span><span class="">= </span><span class="hljs-number">0</span><span class="">;</span></div>
<div class="line" lang="c" id="LC1009"></div>
<div class="line" lang="c" id="LC1010"><span class="">	result </span><span class="">= zmodem_recv_data</span><span class="">(zm, zm-&gt;rx_data_subpacket, </span><span class="hljs-keyword">sizeof</span><span class="">(zm-&gt;rx_data_subpacket)</span><span class="">, &amp;len, ack, type)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC1011"><span class="">	</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(result != FRAMEOK &amp;&amp; result != ENDOFFRAME)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC1012"><span class="">		lprintf</span><span class="">(zm, LOG_DEBUG, </span><span class="hljs-string">"%lu %s ERROR: %s (subpacket type: %s, %u bytes)"</span></div>
<div class="line" lang="c" id="LC1013"><span class="">		        , </span><span class="">(ulong)</span><span class="">zm-&gt;ack_file_pos, __FUNCTION__, chr</span><span class="">(result)</span><span class="">, chr</span><span class="">(*type)</span><span class="">, len)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC1014"><span class="">		zmodem_send_znak</span><span class="">(zm)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC1015"><span class="">		</span><span class="hljs-keyword">return</span><span class=""> FALSE;</span></div>
<div class="line" lang="c" id="LC1016"><span class="">	}</span></div>
<div class="line" lang="c" id="LC1017"></div>
<div class="line" lang="c" id="LC1018"><span class="">	</span><span class="hljs-keyword">return</span><span class=""> TRUE;</span></div>
<div class="line" lang="c" id="LC1019"><span class="">}</span></div>
<div class="line" lang="c" id="LC1020"></div>
<div class="line" lang="c" id="LC1021"><span class="hljs-type">int</span><span class=""> </span><span class="hljs-title.function">zmodem_recv_nibble</span><span class="hljs-params"><span class="hljs-params">(</span><span class="hljs-type">zmodem_t</span><span class="hljs-params">* zm)</span></span></div>
<div class="line" lang="c" id="LC1022"><span class="">{</span></div>
<div class="line" lang="c" id="LC1023"><span class="">	</span><span class="hljs-type">int</span><span class=""> c;</span></div>
<div class="line" lang="c" id="LC1024"></div>
<div class="line" lang="c" id="LC1025"><span class="">	c </span><span class="">= zmodem_rx</span><span class="">(zm)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC1026"></div>
<div class="line" lang="c" id="LC1027"><span class="">	</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(c &lt; </span><span class="hljs-number">0</span><span class="">)</span></div>
<div class="line" lang="c" id="LC1028"><span class="">		</span><span class="hljs-keyword">return</span><span class=""> c;</span></div>
<div class="line" lang="c" id="LC1029"></div>
<div class="line" lang="c" id="LC1030"><span class="">	c </span><span class="">= STRIPPED_PARITY</span><span class="">(c)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC1031"><span class="">	</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(c &gt; </span><span class="hljs-string">'9'</span><span class="">)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC1032"><span class="">		</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(c &lt; </span><span class="hljs-string">'a'</span><span class=""> || c &gt; </span><span class="hljs-string">'f'</span><span class="">)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC1033"><span class="">			</span><span class="hljs-comment">/*</span></div>
<div class="line" lang="c" id="LC1034"><span class="hljs-comment">			 * illegal hex; different than expected.</span></div>
<div class="line" lang="c" id="LC1035"><span class="hljs-comment">			 * we might as well time out.</span></div>
<div class="line" lang="c" id="LC1036"><span class="hljs-comment">			 */</span></div>
<div class="line" lang="c" id="LC1037"><span class="">			</span><span class="hljs-keyword">return</span><span class=""> </span><span class="hljs-number">-1</span><span class="">;</span></div>
<div class="line" lang="c" id="LC1038"><span class="">		}</span></div>
<div class="line" lang="c" id="LC1039"></div>
<div class="line" lang="c" id="LC1040"><span class="">		c -</span><span class="">= </span><span class="hljs-string">'a'</span><span class=""> - </span><span class="hljs-number">10</span><span class="">;</span></div>
<div class="line" lang="c" id="LC1041"><span class="">	}</span></div>
<div class="line" lang="c" id="LC1042"><span class="">	</span><span class="hljs-keyword">else</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC1043"><span class="">		</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(c &lt; </span><span class="hljs-string">'0'</span><span class="">)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC1044"><span class="">			</span><span class="hljs-comment">/*</span></div>
<div class="line" lang="c" id="LC1045"><span class="hljs-comment">			 * illegal hex; different than expected.</span></div>
<div class="line" lang="c" id="LC1046"><span class="hljs-comment">			 * we might as well time out.</span></div>
<div class="line" lang="c" id="LC1047"><span class="hljs-comment">			 */</span></div>
<div class="line" lang="c" id="LC1048"><span class="">			</span><span class="hljs-keyword">return</span><span class=""> </span><span class="hljs-number">-1</span><span class="">;</span></div>
<div class="line" lang="c" id="LC1049"><span class="">		}</span></div>
<div class="line" lang="c" id="LC1050"><span class="">		c -</span><span class="">= </span><span class="hljs-string">'0'</span><span class="">;</span></div></code></pre></div></div><div class="gl-flex"><div class="gl-absolute gl-flex gl-flex-col"><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1051" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1051" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1051" data-line-number="1051" class="file-line-num gl-select-none !gl-shadow-none">
        1051
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1052" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1052" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1052" data-line-number="1052" class="file-line-num gl-select-none !gl-shadow-none">
        1052
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1053" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1053" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1053" data-line-number="1053" class="file-line-num gl-select-none !gl-shadow-none">
        1053
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1054" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1054" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1054" data-line-number="1054" class="file-line-num gl-select-none !gl-shadow-none">
        1054
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1055" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1055" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1055" data-line-number="1055" class="file-line-num gl-select-none !gl-shadow-none">
        1055
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1056" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1056" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1056" data-line-number="1056" class="file-line-num gl-select-none !gl-shadow-none">
        1056
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1057" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1057" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1057" data-line-number="1057" class="file-line-num gl-select-none !gl-shadow-none">
        1057
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1058" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1058" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1058" data-line-number="1058" class="file-line-num gl-select-none !gl-shadow-none">
        1058
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1059" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1059" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1059" data-line-number="1059" class="file-line-num gl-select-none !gl-shadow-none">
        1059
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1060" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1060" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1060" data-line-number="1060" class="file-line-num gl-select-none !gl-shadow-none">
        1060
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1061" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1061" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1061" data-line-number="1061" class="file-line-num gl-select-none !gl-shadow-none">
        1061
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1062" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1062" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1062" data-line-number="1062" class="file-line-num gl-select-none !gl-shadow-none">
        1062
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1063" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1063" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1063" data-line-number="1063" class="file-line-num gl-select-none !gl-shadow-none">
        1063
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1064" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1064" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1064" data-line-number="1064" class="file-line-num gl-select-none !gl-shadow-none">
        1064
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1065" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1065" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1065" data-line-number="1065" class="file-line-num gl-select-none !gl-shadow-none">
        1065
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1066" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1066" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1066" data-line-number="1066" class="file-line-num gl-select-none !gl-shadow-none">
        1066
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1067" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1067" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1067" data-line-number="1067" class="file-line-num gl-select-none !gl-shadow-none">
        1067
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1068" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1068" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1068" data-line-number="1068" class="file-line-num gl-select-none !gl-shadow-none">
        1068
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1069" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1069" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1069" data-line-number="1069" class="file-line-num gl-select-none !gl-shadow-none">
        1069
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1070" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1070" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1070" data-line-number="1070" class="file-line-num gl-select-none !gl-shadow-none">
        1070
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1071" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1071" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1071" data-line-number="1071" class="file-line-num gl-select-none !gl-shadow-none">
        1071
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1072" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1072" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1072" data-line-number="1072" class="file-line-num gl-select-none !gl-shadow-none">
        1072
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1073" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1073" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1073" data-line-number="1073" class="file-line-num gl-select-none !gl-shadow-none">
        1073
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1074" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1074" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1074" data-line-number="1074" class="file-line-num gl-select-none !gl-shadow-none">
        1074
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1075" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1075" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1075" data-line-number="1075" class="file-line-num gl-select-none !gl-shadow-none">
        1075
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1076" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1076" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1076" data-line-number="1076" class="file-line-num gl-select-none !gl-shadow-none">
        1076
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1077" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1077" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1077" data-line-number="1077" class="file-line-num gl-select-none !gl-shadow-none">
        1077
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1078" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1078" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1078" data-line-number="1078" class="file-line-num gl-select-none !gl-shadow-none">
        1078
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1079" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1079" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1079" data-line-number="1079" class="file-line-num gl-select-none !gl-shadow-none">
        1079
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1080" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1080" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1080" data-line-number="1080" class="file-line-num gl-select-none !gl-shadow-none">
        1080
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1081" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1081" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1081" data-line-number="1081" class="file-line-num gl-select-none !gl-shadow-none">
        1081
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1082" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1082" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1082" data-line-number="1082" class="file-line-num gl-select-none !gl-shadow-none">
        1082
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1083" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1083" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1083" data-line-number="1083" class="file-line-num gl-select-none !gl-shadow-none">
        1083
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1084" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1084" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1084" data-line-number="1084" class="file-line-num gl-select-none !gl-shadow-none">
        1084
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1085" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1085" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1085" data-line-number="1085" class="file-line-num gl-select-none !gl-shadow-none">
        1085
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1086" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1086" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1086" data-line-number="1086" class="file-line-num gl-select-none !gl-shadow-none">
        1086
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1087" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1087" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1087" data-line-number="1087" class="file-line-num gl-select-none !gl-shadow-none">
        1087
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1088" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1088" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1088" data-line-number="1088" class="file-line-num gl-select-none !gl-shadow-none">
        1088
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1089" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1089" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1089" data-line-number="1089" class="file-line-num gl-select-none !gl-shadow-none">
        1089
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1090" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1090" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1090" data-line-number="1090" class="file-line-num gl-select-none !gl-shadow-none">
        1090
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1091" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1091" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1091" data-line-number="1091" class="file-line-num gl-select-none !gl-shadow-none">
        1091
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1092" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1092" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1092" data-line-number="1092" class="file-line-num gl-select-none !gl-shadow-none">
        1092
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1093" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1093" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1093" data-line-number="1093" class="file-line-num gl-select-none !gl-shadow-none">
        1093
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1094" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1094" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1094" data-line-number="1094" class="file-line-num gl-select-none !gl-shadow-none">
        1094
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1095" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1095" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1095" data-line-number="1095" class="file-line-num gl-select-none !gl-shadow-none">
        1095
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1096" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1096" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1096" data-line-number="1096" class="file-line-num gl-select-none !gl-shadow-none">
        1096
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1097" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1097" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1097" data-line-number="1097" class="file-line-num gl-select-none !gl-shadow-none">
        1097
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1098" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1098" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1098" data-line-number="1098" class="file-line-num gl-select-none !gl-shadow-none">
        1098
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1099" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1099" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1099" data-line-number="1099" class="file-line-num gl-select-none !gl-shadow-none">
        1099
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1100" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1100" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1100" data-line-number="1100" class="file-line-num gl-select-none !gl-shadow-none">
        1100
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1101" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1101" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1101" data-line-number="1101" class="file-line-num gl-select-none !gl-shadow-none">
        1101
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1102" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1102" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1102" data-line-number="1102" class="file-line-num gl-select-none !gl-shadow-none">
        1102
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1103" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1103" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1103" data-line-number="1103" class="file-line-num gl-select-none !gl-shadow-none">
        1103
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1104" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1104" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1104" data-line-number="1104" class="file-line-num gl-select-none !gl-shadow-none">
        1104
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1105" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1105" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1105" data-line-number="1105" class="file-line-num gl-select-none !gl-shadow-none">
        1105
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1106" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1106" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1106" data-line-number="1106" class="file-line-num gl-select-none !gl-shadow-none">
        1106
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1107" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1107" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1107" data-line-number="1107" class="file-line-num gl-select-none !gl-shadow-none">
        1107
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1108" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1108" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1108" data-line-number="1108" class="file-line-num gl-select-none !gl-shadow-none">
        1108
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1109" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1109" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1109" data-line-number="1109" class="file-line-num gl-select-none !gl-shadow-none">
        1109
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1110" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1110" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1110" data-line-number="1110" class="file-line-num gl-select-none !gl-shadow-none">
        1110
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1111" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1111" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1111" data-line-number="1111" class="file-line-num gl-select-none !gl-shadow-none">
        1111
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1112" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1112" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1112" data-line-number="1112" class="file-line-num gl-select-none !gl-shadow-none">
        1112
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1113" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1113" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1113" data-line-number="1113" class="file-line-num gl-select-none !gl-shadow-none">
        1113
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1114" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1114" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1114" data-line-number="1114" class="file-line-num gl-select-none !gl-shadow-none">
        1114
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1115" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1115" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1115" data-line-number="1115" class="file-line-num gl-select-none !gl-shadow-none">
        1115
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1116" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1116" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1116" data-line-number="1116" class="file-line-num gl-select-none !gl-shadow-none">
        1116
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1117" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1117" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1117" data-line-number="1117" class="file-line-num gl-select-none !gl-shadow-none">
        1117
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1118" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1118" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1118" data-line-number="1118" class="file-line-num gl-select-none !gl-shadow-none">
        1118
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1119" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1119" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1119" data-line-number="1119" class="file-line-num gl-select-none !gl-shadow-none">
        1119
      </a></div><div data-testid="line-numbers" class="diff-line-num line-links line-numbers gl-border-r gl-z-3 gl-flex !gl-p-0"><a data-event-tracking="click_chunk_blame_on_blob_page" href="https://gitlab.synchro.net/main/sbbs/-/blame/master/src/sbbs3/zmodem.c?ref_type=heads#L1120" class="file-line-blame gl-select-none !gl-shadow-none"></a> <a id="L1120" href="https://gitlab.synchro.net/main/sbbs/-/blob/master/src/sbbs3/zmodem.c?ref_type=heads#L1120" data-line-number="1120" class="file-line-num gl-select-none !gl-shadow-none">
        1120
      </a></div></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" style="margin-left: 96px;"><div class="line" lang="c" id="LC1051"><span class="">	}</span></div>
<div class="line" lang="c" id="LC1052"></div>
<div class="line" lang="c" id="LC1053"><span class="">	</span><span class="hljs-keyword">return</span><span class=""> c;</span></div>
<div class="line" lang="c" id="LC1054"><span class="">}</span></div>
<div class="line" lang="c" id="LC1055"></div>
<div class="line" lang="c" id="LC1056"><span class="hljs-type">int</span><span class=""> </span><span class="hljs-title.function">zmodem_recv_hex</span><span class="hljs-params"><span class="hljs-params">(</span><span class="hljs-type">zmodem_t</span><span class="hljs-params">* zm)</span></span></div>
<div class="line" lang="c" id="LC1057"><span class="">{</span></div>
<div class="line" lang="c" id="LC1058"><span class="">	</span><span class="hljs-type">int</span><span class=""> n1;</span></div>
<div class="line" lang="c" id="LC1059"><span class="">	</span><span class="hljs-type">int</span><span class=""> n0;</span></div>
<div class="line" lang="c" id="LC1060"><span class="">	</span><span class="hljs-type">int</span><span class=""> ret;</span></div>
<div class="line" lang="c" id="LC1061"></div>
<div class="line" lang="c" id="LC1062"><span class="">	n1 </span><span class="">= zmodem_recv_nibble</span><span class="">(zm)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC1063"><span class="">	</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(n1 &lt; </span><span class="hljs-number">0</span><span class="">)</span></div>
<div class="line" lang="c" id="LC1064"><span class="">		</span><span class="hljs-keyword">return</span><span class=""> n1;</span></div>
<div class="line" lang="c" id="LC1065"><span class="">	n0 </span><span class="">= zmodem_recv_nibble</span><span class="">(zm)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC1066"><span class="">	</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(n0 &lt; </span><span class="hljs-number">0</span><span class="">)</span></div>
<div class="line" lang="c" id="LC1067"><span class="">		</span><span class="hljs-keyword">return</span><span class=""> n0;</span></div>
<div class="line" lang="c" id="LC1068"></div>
<div class="line" lang="c" id="LC1069"><span class="">	</span><span class="hljs-comment">// coverity[overflow:SUPPRESS]</span></div>
<div class="line" lang="c" id="LC1070"><span class="">	ret </span><span class="">= </span><span class="">(n1 &lt;&lt; </span><span class="hljs-number">4</span><span class="">)</span><span class=""> | n0;</span></div>
<div class="line" lang="c" id="LC1071"></div>
<div class="line" lang="c" id="LC1072"><span class="hljs-comment">//	lprintf(zm,LOG_DEBUG, __FUNCTION__ " returning: 0x%02X", ret);</span></div>
<div class="line" lang="c" id="LC1073"></div>
<div class="line" lang="c" id="LC1074"><span class="">	</span><span class="hljs-keyword">return</span><span class=""> ret;</span></div>
<div class="line" lang="c" id="LC1075"><span class="">}</span></div>
<div class="line" lang="c" id="LC1076"></div>
<div class="line" lang="c" id="LC1077"><span class="hljs-comment"><span class="hljs-comment">/*</span></span></div>
<div class="line" lang="c" id="LC1078"><span class="hljs-comment"> *</span><span class="hljs-comment"> receive routines for </span><span class="hljs-comment">each of</span><span class="hljs-comment"> the six different </span><span class="hljs-comment">styles of header.</span></div>
<div class="line" lang="c" id="LC1079"><span class="hljs-comment"> * each of these leaves zm-&gt;rxd_header_len set to 0</span><span class="hljs-comment"> if the end </span><span class="hljs-comment">result is</span></div>
<div class="line" lang="c" id="LC1080"><span class="hljs-comment"> *</span><span class="hljs-comment"> not a valid </span><span class="hljs-comment">header.</span></div>
<div class="line" lang="c" id="LC1081"><span class="hljs-comment"> */</span></div>
<div class="line" lang="c" id="LC1082"></div>
<div class="line" lang="c" id="LC1083"><span class="">BOOL </span><span class="hljs-title.function">zmodem_recv_bin16_header</span><span class="hljs-params"><span class="hljs-params">(</span><span class="hljs-type">zmodem_t</span><span class="hljs-params">* zm)</span></span></div>
<div class="line" lang="c" id="LC1084"><span class="">{</span></div>
<div class="line" lang="c" id="LC1085"><span class="">	</span><span class="hljs-type">int</span><span class="">                c;</span></div>
<div class="line" lang="c" id="LC1086"><span class="">	</span><span class="hljs-type">int</span><span class="">                n;</span></div>
<div class="line" lang="c" id="LC1087"><span class="">	</span><span class="hljs-type">unsigned</span><span class=""> </span><span class="hljs-type">short</span><span class=""> </span><span class="hljs-type">int</span><span class=""> crc;</span></div>
<div class="line" lang="c" id="LC1088"><span class="">	</span><span class="hljs-type">unsigned</span><span class=""> </span><span class="hljs-type">short</span><span class=""> </span><span class="hljs-type">int</span><span class=""> rxd_crc;</span></div>
<div class="line" lang="c" id="LC1089"></div>
<div class="line" lang="c" id="LC1090"><span class="hljs-comment">//	lprintf(zm ,LOG_DEBUG, __FUNCTION__);</span></div>
<div class="line" lang="c" id="LC1091"></div>
<div class="line" lang="c" id="LC1092"><span class="">	crc </span><span class="">= </span><span class="hljs-number">0</span><span class="">;</span></div>
<div class="line" lang="c" id="LC1093"></div>
<div class="line" lang="c" id="LC1094"><span class="">	</span><span class="hljs-keyword">for</span><span class=""> </span><span class="">(n = </span><span class="hljs-number">0</span><span class="">; n &lt; HDRLEN; n++)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC1095"><span class="">		c </span><span class="">= zmodem_rx</span><span class="">(zm)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC1096"><span class="">		</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(c &lt; </span><span class="hljs-number">0</span><span class="">)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC1097"><span class="">			lprintf</span><span class="">(zm, LOG_WARNING, </span><span class="hljs-string">"%lu %s ERROR: %s"</span></div>
<div class="line" lang="c" id="LC1098"><span class="">			        , </span><span class="">(ulong)</span><span class="">zm-&gt;current_file_pos, __FUNCTION__, chr</span><span class="">(c)</span><span class="">)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC1099"><span class="">			</span><span class="hljs-keyword">return</span><span class=""> FALSE;</span></div>
<div class="line" lang="c" id="LC1100"><span class="">		}</span></div>
<div class="line" lang="c" id="LC1101"><span class="">		crc </span><span class="">= ucrc16</span><span class="">(c, crc)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC1102"><span class="">		zm-&gt;rxd_header[n] </span><span class="">= c;</span></div>
<div class="line" lang="c" id="LC1103"><span class="">	}</span></div>
<div class="line" lang="c" id="LC1104"></div>
<div class="line" lang="c" id="LC1105"><span class="">	rxd_crc  </span><span class="">= zmodem_rx</span><span class="">(zm)</span><span class=""> &lt;&lt; </span><span class="hljs-number">8</span><span class="">;</span></div>
<div class="line" lang="c" id="LC1106"><span class="">	rxd_crc |</span><span class="">= zmodem_rx</span><span class="">(zm)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC1107"></div>
<div class="line" lang="c" id="LC1108"><span class="">	</span><span class="hljs-keyword">if</span><span class=""> </span><span class="">(rxd_crc != crc)</span><span class=""> {</span></div>
<div class="line" lang="c" id="LC1109"><span class="">		lprintf</span><span class="">(zm, LOG_WARNING, </span><span class="hljs-string">"%lu %s CRC ERROR: 0x%hX, expected: 0x%hX"</span></div>
<div class="line" lang="c" id="LC1110"><span class="">		        , </span><span class="">(ulong)</span><span class="">zm-&gt;ack_file_pos, __FUNCTION__, rxd_crc, crc)</span><span class="">;</span></div>
<div class="line" lang="c" id="LC1111"><span class="">		</span><span class="hljs-keyword">return</span><span class=""> FALSE;</span></div>
<div class="line" lang="c" id="LC1112"><span class="">	}</span></div>
<div class="line" lang="c" id="LC1113"><span class="hljs-comment">//	lprintf(zm,LOG_DEBUG, "%lu %s GOOD CRC: %04hX", __FUNCTION__</span></div>
<div class="line" lang="c" id="LC1114"><span class="hljs-comment">//		,(ulong)zm-&gt;ack_file_pos, __FUNCTION__, crc);</span></div>
<div class="line" lang="c" id="LC1115"></div>
<div class="line" lang="c" id="LC1116"><span class="">	zm-&gt;rxd_header_len </span><span class="">= n;</span></div>
<div class="line" lang="c" id="LC1117"></div>
<div class="line" lang="c" id="LC1118"><span class="">	</span><span class="hljs-keyword">return</span><span class=""> TRUE;</span></div>
<div class="line" lang="c" id="LC1119"><span class="">}</span></div>
<div class="line" lang="c" id="LC1120"></div></code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">BOOL zmodem_recv_hex_header(zmodem_t* zm)
{
	int                c;
	int                i;
	unsigned short int crc = 0;
	unsigned short int rxd_crc;

//	lprintf(zm, LOG_DEBUG, __FUNCTION__);

	for (i = 0; i &lt; HDRLEN; i++) {
		c = zmodem_recv_hex(zm);
		if (c &lt; 0)
			return FALSE;
		crc = ucrc16(c, crc);

		zm-&gt;rxd_header[i] = c;
	}

	/*
	 * receive the crc
	 */

	c = zmodem_recv_hex(zm);

	if (c &lt; 0)
		return FALSE;

	rxd_crc = c &lt;&lt; 8;

	c = zmodem_recv_hex(zm);

	if (c &lt; 0)
		return FALSE;

	rxd_crc |= c;

	if (rxd_crc == crc) {
//		lprintf(zm,LOG_DEBUG, "%s GOOD CRC: %04hX", __FUNCTION__, crc);
		zm-&gt;rxd_header_len = i;
	}
	else {
		lprintf(zm, LOG_WARNING, "%s CRC ERROR: 0x%hX, expected: 0x%hX"
		        , __FUNCTION__, rxd_crc, crc);
		return FALSE;
	}

	/*
	 * drop the end of line sequence after a hex header
	 */
	c = zmodem_rx(zm);
	if (c == '\r' || c == SET_PARITY('\r')) { // CR with Even Parity (Tera Term's ZMODEM sends this)
		/*
		 * both bytes are expected when the first received is a CR
		 */
		c = zmodem_rx(zm);  /* drop LF */
	}
	if (c != '\n' &amp;&amp; c != SET_PARITY('\n')) { // LF with Odd Parity
		lprintf(zm, LOG_ERR, "%s HEX header not terminated with LF: %s"
		        , __FUNCTION__, chr(c));
		return FALSE;
	}

	return TRUE;
}

BOOL zmodem_recv_bin32_header(zmodem_t* zm)
{
	int      c;
	int      n;
	uint32_t crc;</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">	uint32_t rxd_crc;

//	lprintf(zm,LOG_DEBUG,"recv_bin32_header");

	crc = 0xffffffffL;

	for (n = 0; n &lt; HDRLEN; n++) {
		c = zmodem_rx(zm);
		if (c &lt; 0)
			return TRUE;
		crc = ucrc32(c, crc);
		zm-&gt;rxd_header[n] = c;
	}

	crc = ~crc;

	rxd_crc  = zmodem_rx(zm);
	rxd_crc |= zmodem_rx(zm) &lt;&lt; 8;
	rxd_crc |= zmodem_rx(zm) &lt;&lt; 16;
	rxd_crc |= zmodem_rx(zm) &lt;&lt; 24;

	if (rxd_crc != crc) {
		lprintf(zm, LOG_WARNING, "%lu %s CRC ERROR (%08X, expected: %08X)"
		        , (ulong)zm-&gt;ack_file_pos, __FUNCTION__, rxd_crc, crc);
		return FALSE;
	}
//	lprintf(zm,LOG_DEBUG, "%lu %s GOOD CRC: %08lX", (ulong)zm-&gt;ack_file_pos, __FUNCTION__, crc);

	zm-&gt;rxd_header_len = n;
	return TRUE;
}

/*
 * receive any style header
 * a flag (receive_32bit_data) will be set to indicate whether data
 * packets following this header will have 16 or 32 bit data attached.
 * variable headers are not implemented.
 */

int zmodem_recv_header_raw(zmodem_t* zm)
{
	int      c;
	int      type = INVALIDSUBPKT;
	int      frame_type;
	uint64_t freespace;

//	lprintf(zm,LOG_DEBUG, __FUNCTION__);

	zm-&gt;rxd_header_len = 0;

	do {
		do {
			if ((c = zmodem_recv_raw(zm)) &lt; 0)
				return c;
			if (is_cancelled(zm))
				return ZCAN;
		} while (STRIPPED_PARITY(c) != ZPAD);

		if ((c = zmodem_recv_raw(zm)) &lt; 0)
			return c;

		if (STRIPPED_PARITY(c) == ZPAD) {
			if ((c = zmodem_recv_raw(zm)) &lt; 0)
				return c;
		}

		/*
		 * spurious ZPAD check
		 */
</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">		if (STRIPPED_PARITY(c) != ZDLE) {
			lprintf(zm, LOG_DEBUG, "%s Expected ZDLE, received: %s", __FUNCTION__, chr(c));
			continue;
		}

		/*
		 * now read the header style
		 */

		c = zmodem_rx(zm);

		switch (STRIPPED_PARITY(c)) {
			case ZBIN:
				if (!zmodem_recv_bin16_header(zm))
					return INVHDR;
				zm-&gt;receive_32bit_data = FALSE;
				break;
			case ZHEX:
				if (!zmodem_recv_hex_header(zm))
					return INVHDR;
				zm-&gt;receive_32bit_data = FALSE;
				break;
			case ZBIN32:
				if (!zmodem_recv_bin32_header(zm))
					return INVHDR;
				zm-&gt;receive_32bit_data = TRUE;
				break;
			default:
				if (c &lt; 0) {
					lprintf(zm, LOG_WARNING, "%lu %s ERROR: %s"
					        , (ulong)zm-&gt;current_file_pos, __FUNCTION__, chr(c));
					return c;
				}
				/*
				 * unrecognized header style
				 */
				lprintf(zm, LOG_ERR, "%lu %s UNRECOGNIZED header: %s"
				        , (ulong)zm-&gt;current_file_pos, __FUNCTION__, chr(c));
				continue;
		}

	} while (zm-&gt;rxd_header_len == 0 &amp;&amp; !is_cancelled(zm));

	if (is_cancelled(zm))
		return ZCAN;

	/*
	 * this appears to have been a valid header.
	 * return its type.
	 */

	frame_type = zm-&gt;rxd_header[0];

	zm-&gt;rxd_header_pos = zm-&gt;rxd_header[ZP0] | (zm-&gt;rxd_header[ZP1] &lt;&lt; 8) |
	                     (zm-&gt;rxd_header[ZP2] &lt;&lt; 16) | (zm-&gt;rxd_header[ZP3] &lt;&lt; 24);

	switch (frame_type) {
		case ZCRC:
			zm-&gt;crc_request = zm-&gt;rxd_header_pos;
			break;
		case ZDATA:
			zm-&gt;ack_file_pos = zm-&gt;rxd_header_pos;
			break;
		case ZFILE:
			zm-&gt;ack_file_pos = 0l;
			if (!zmodem_recv_subpacket(zm, /* ack? */ FALSE, &amp;type)) {
				lprintf(zm, LOG_WARNING, "%s bad %s subpacket: %s", __FUNCTION__, chr(frame_type), chr(type));
				frame_type |= BADSUBPKT;
			}
			break;</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">		case ZSINIT:
		case ZCOMMAND:
			if (!zmodem_recv_subpacket(zm, /* ack? */ TRUE, &amp;type)) {
				lprintf(zm, LOG_WARNING, "%s bad %s subpacket: %s", __FUNCTION__, chr(frame_type), chr(type));
				frame_type |= BADSUBPKT;
			}
			break;
		case ZFREECNT:
			freespace = getfreediskspace(".", 1);
			zmodem_send_pos_header(zm, ZACK, (uint32_t)(freespace &gt; UINT32_MAX ? UINT32_MAX : freespace), /* Hex? */ TRUE);
			break;
	}

#if 0 /* def _DEBUG */
	lprintf(zm, LOG_DEBUG, __FUNCTION__ " received header type: %s"
	        , frame_desc(frame_type));
#endif

	return frame_type;
}

int zmodem_recv_header(zmodem_t* zm)
{
	int ret;

	switch (ret = zmodem_recv_header_raw(zm)) {
		case TIMEOUT:
			lprintf(zm, LOG_WARNING, "%s TIMEOUT", __FUNCTION__);
			break;
		case INVHDR:
			lprintf(zm, LOG_WARNING, "%s detected an INVALID HEADER", __FUNCTION__);
			break;
		default:
			lprintf(zm, LOG_DEBUG, "%lu %s frame: %s"
			        , (ulong)frame_pos(zm, ret), __FUNCTION__, frame_desc(ret));
			if (ret == ZCAN)
				zm-&gt;cancelled = TRUE;
			else if (ret == ZRINIT)
				zmodem_parse_zrinit(zm);
			break;
	}

	return ret;
}

BOOL zmodem_request_crc(zmodem_t* zm, int32_t length)
{
	zmodem_recv_purge(zm, /* timeout: */ 0);
	zmodem_send_pos_header(zm, ZCRC, length, /* HEX: */ TRUE);
	return TRUE;
}

BOOL zmodem_recv_crc(zmodem_t* zm, uint32_t* crc)
{
	int type;

	if (!is_data_waiting(zm, zm-&gt;crc_timeout)) {
		lprintf(zm, LOG_ERR, "%lu %s Timeout waiting for response (%u seconds)"
		        , (ulong)zm-&gt;current_file_pos, __FUNCTION__, zm-&gt;crc_timeout);
		return FALSE;
	}
	if ((type = zmodem_recv_header(zm)) != ZCRC) {
		lprintf(zm, LOG_ERR, "%lu %s Received %s instead of ZCRC"
		        , (ulong)zm-&gt;current_file_pos, __FUNCTION__, frame_desc(type));
		return FALSE;
	}
	if (crc != NULL)
		*crc = zm-&gt;crc_request;
	return TRUE;
}</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">
BOOL zmodem_get_crc(zmodem_t* zm, int32_t length, uint32_t* crc)
{
	if (zmodem_request_crc(zm, length))
		return zmodem_recv_crc(zm, crc);
	return FALSE;
}

void zmodem_parse_zrinit(zmodem_t* zm)
{
	zm-&gt;can_full_duplex                 = INT_TO_BOOL(zm-&gt;rxd_header[ZF0] &amp; ZF0_CANFDX);
	zm-&gt;can_overlap_io                  = INT_TO_BOOL(zm-&gt;rxd_header[ZF0] &amp; ZF0_CANOVIO);
	zm-&gt;can_break                       = INT_TO_BOOL(zm-&gt;rxd_header[ZF0] &amp; ZF0_CANBRK);
	zm-&gt;can_fcs_32                      = INT_TO_BOOL(zm-&gt;rxd_header[ZF0] &amp; ZF0_CANFC32);
	zm-&gt;escape_ctrl_chars               = INT_TO_BOOL(zm-&gt;rxd_header[ZF0] &amp; ZF0_ESCCTL);
	zm-&gt;escape_8th_bit                  = INT_TO_BOOL(zm-&gt;rxd_header[ZF0] &amp; ZF0_ESC8);

	lprintf(zm, LOG_INFO, "Receiver requested mode (0x%02X):\r\n"
	        "%s-duplex, %s overlap I/O, CRC-%u, Escape: %s"
	        , zm-&gt;rxd_header[ZF0]
	        , zm-&gt;can_full_duplex ? "Full" : "Half"
	        , zm-&gt;can_overlap_io ? "Can" : "Cannot"
	        , zm-&gt;can_fcs_32 ? 32 : 16
	        , zm-&gt;escape_ctrl_chars ? "ALL" : "Normal"
	        );

	if ((zm-&gt;recv_bufsize = (zm-&gt;rxd_header[ZP0] | zm-&gt;rxd_header[ZP1] &lt;&lt; 8)) != 0)
		lprintf(zm, LOG_INFO, "Receiver specified buffer size of: %u", zm-&gt;recv_bufsize);
}

int zmodem_get_zrinit(zmodem_t* zm)
{
	unsigned char zrqinit_header[] = { ZRQINIT, /* ZF3: */ 0, 0, 0, /* ZF0: */ 0 };
	/* Note: sz/dsz/fdsz sends 0x80 in ZF3 because it supports var-length headers. */
	/* We do not, so we send 0x00, resulting in a CRC-16 value of 0x0000 as well. */

	lprintf(zm, LOG_DEBUG, __FUNCTION__);
	zmodem_send_raw(zm, 'r');
	zmodem_send_raw(zm, 'z');
	zmodem_send_raw(zm, '\r');
	zmodem_send_hex_header(zm, zrqinit_header);

	if (!is_data_waiting(zm, zm-&gt;init_timeout))
		return TIMEOUT;
	return zmodem_recv_header(zm);
}

int zmodem_send_zrinit(zmodem_t* zm)
{
	unsigned char zrinit_header[] = { ZRINIT, 0, 0, 0, 0 };

	if (zm-&gt;can_full_duplex)
		zrinit_header[ZF0] = ZF0_CANFDX;

	if (!zm-&gt;no_streaming)
		zrinit_header[ZF0] |= ZF0_CANOVIO;

	if (zm-&gt;can_break)
		zrinit_header[ZF0] |= ZF0_CANBRK;

	if (!zm-&gt;want_fcs_16)
		zrinit_header[ZF0] |= ZF0_CANFC32;

	if (zm-&gt;escape_ctrl_chars)
		zrinit_header[ZF0] |= ZF0_ESCCTL;

	if (zm-&gt;escape_8th_bit)
		zrinit_header[ZF0] |= ZF0_ESC8;

	if (zm-&gt;no_streaming &amp;&amp; zm-&gt;recv_bufsize == 0)</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">		zm-&gt;recv_bufsize = zm-&gt;max_block_size;

	zrinit_header[ZP0] = zm-&gt;recv_bufsize &amp; 0xff;
	zrinit_header[ZP1] = zm-&gt;recv_bufsize &gt;&gt; 8;

	return zmodem_send_hex_header(zm, zrinit_header);
}

/* Returns ZFIN on success */
int zmodem_get_zfin(zmodem_t* zm)
{
	int      result;
	int      type = ZCAN;
	unsigned attempts;

	lprintf(zm, LOG_DEBUG, __FUNCTION__);

	for (attempts = 0; attempts &lt; zm-&gt;max_errors &amp;&amp; is_connected(zm) &amp;&amp; !is_cancelled(zm); attempts++) {
		if (attempts &amp; 1)  /* Alternate between ZABORT and ZFIN */
			result = zmodem_send_zabort(zm);
		else
			result = zmodem_send_zfin(zm);
		if (result != SEND_SUCCESS)
			return result;
		if ((type = zmodem_recv_header(zm)) == ZFIN)
			break;
	}

	/*
	 * these Os are formally required; but they don't do a thing
	 * unfortunately many programs require them to exit
	 * (both programs already sent a ZFIN so why bother ?)
	 */

	if (type == ZFIN) {
		zmodem_send_raw(zm, 'O');
		zmodem_send_raw(zm, 'O');
	}

	return type;
}

BOOL zmodem_handle_zrpos(zmodem_t* zm, uint64_t* pos)
{
	if (zm-&gt;rxd_header_pos &lt; zm-&gt;current_file_size) {
		if (*pos != zm-&gt;rxd_header_pos) {
			*pos = zm-&gt;rxd_header_pos;
			zm-&gt;ack_file_pos = (int32_t)*pos;
			lprintf(zm, LOG_INFO, "%lu Resuming transfer from offset: %" PRIu64
			        , (ulong)zm-&gt;current_file_pos, *pos);
		}
		zmodem_recv_purge(zm, /* timeout: */ 1);
		return TRUE;
	}
	lprintf(zm, LOG_WARNING, "%lu Received INVALID ZRPOS offset: %u"
	        , (ulong)zm-&gt;current_file_pos, zm-&gt;rxd_header_pos);
	return FALSE;
}

BOOL zmodem_handle_zack(zmodem_t* zm, uint32_t min, uint32_t max)
{
	if (zm-&gt;rxd_header_pos &gt;= min &amp;&amp; zm-&gt;rxd_header_pos &lt;= max) {
		lprintf(zm, LOG_DEBUG, "%lu Received valid ZACK", (ulong)zm-&gt;rxd_header_pos);
		zm-&gt;ack_file_pos = zm-&gt;rxd_header_pos;
		return TRUE;
	}
	lprintf(zm, LOG_WARNING, "%lu Received INVALID ZACK, offset: %u"
	        , (ulong)zm-&gt;current_file_pos, zm-&gt;rxd_header_pos);
	return FALSE;
}</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">
static uint64_t new_window_size(zmodem_t* zm, time_t start, unsigned pos)
{
	time_t   elapsed = time(NULL) - start;
	if (elapsed &lt; 1)
		elapsed = 1;
	uint64_t cps = (uint64_t)(pos / elapsed);
	if (cps &lt; 1)
		cps = 1;
	if (cps &gt; UINT_MAX)
		cps = UINT_MAX;
	if (cps * zm-&gt;target_window_size &gt; UINT_MAX)
		cps = UINT_MAX / zm-&gt;target_window_size;
	return cps * zm-&gt;target_window_size;
}

/*
 * send from the current position in the file
 * all the way to end of file or until something goes wrong.
 * (ZNAK or ZRPOS received)
 * returns ZRINIT on success.
 */

int zmodem_send_from(zmodem_t* zm, FILE* fp, uint64_t pos, uint64_t* sent)
{
	size_t   len;
	uchar    tx_type;
	unsigned buf_sent = 0;
	unsigned subpkts_sent = 0;
	unsigned backchannel_wait = 0;
	time_t   start = time(NULL);

	lprintf(zm, LOG_DEBUG, "%lu %s", (ulong)pos, __FUNCTION__);
	if (sent != NULL)
		*sent = 0;

	if (fseeko(fp, (off_t)pos, SEEK_SET) != 0) {
		lprintf(zm, LOG_ERR, "%s ERROR %d seeking to file offset %" PRIu64
		        , __FUNCTION__, errno, pos);
		zmodem_send_pos_header(zm, ZFERR, (uint32_t)pos, /* Hex? */ TRUE);
		return ZFERR;
	}
	zm-&gt;current_file_pos = pos;

	/*
	 * send the data in the file
	 */

	while (is_connected(zm)) {

		/*
		 * characters from the other side
		 * check out that header
		 */
		if (zm-&gt;consecutive_errors &amp;&amp; backchannel_wait == 0)
			backchannel_wait = 1;
		while (is_data_waiting(zm, backchannel_wait) &amp;&amp; !is_cancelled(zm) &amp;&amp; is_connected(zm)) {
			int rx_type;
			int c;
			lprintf(zm, LOG_DEBUG, "Back-channel traffic detected");
			if ((c = zmodem_recv_raw(zm)) &lt; 0) {
				lprintf(zm, LOG_ERR, "Back-channel receive ERROR: %s", chr(c));
				return c;
			}
			if (c == ZPAD) {
				rx_type = zmodem_recv_header(zm);
				lprintf(zm, LOG_DEBUG, "Received back-channel data: %s", chr(rx_type));
				if (rx_type == ZACK &amp;&amp; zmodem_handle_zack(zm, zm-&gt;ack_file_pos, (uint32_t)zm-&gt;current_file_pos)) {
					zm-&gt;current_window_size = zm-&gt;current_file_pos - zm-&gt;ack_file_pos;
					lprintf(zm, LOG_DEBUG, "%lu Asynchronous acknowledgment (ZACK) of %lu bytes, new window: %lu"</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">					        , (ulong)zm-&gt;current_file_pos, (ulong)zm-&gt;ack_file_pos, (ulong)zm-&gt;current_window_size);
					if (zm-&gt;max_window_size &amp;&amp; zm-&gt;target_window_size) {
						zm-&gt;max_window_size = new_window_size(zm, start, zm-&gt;rxd_header_pos);
						lprintf(zm, LOG_DEBUG, "%lu New window size: %lu (%u seconds of data)"
						        , (ulong)zm-&gt;current_file_pos, (ulong)zm-&gt;max_window_size, zm-&gt;target_window_size);
					}
					continue;
				}
				else if (rx_type &gt;= 0) {
					zmodem_send_data(zm, ZCRCE, /* data: */ NULL, /* len: */ 0);
					return rx_type;
				}
			} else
				lprintf(zm, LOG_INFO, "Unexpected back-channel data received: %s", chr(c));
		}
		if (is_cancelled(zm))
			return ZCAN;

		/*
		 * read a block from the file
		 */
		pos = zm-&gt;current_file_pos;
		if (zm-&gt;max_window_size &amp;&amp; zm-&gt;current_window_size &gt;= zm-&gt;max_window_size) {
			lprintf(zm, LOG_WARNING, "%lu Transmit-Window management: %lu &gt;= %lu"
			        , (ulong)zm-&gt;current_file_pos, (ulong)zm-&gt;current_window_size, (ulong)zm-&gt;max_window_size);
			backchannel_wait = 1;
			continue;
		}

		len = fread(zm-&gt;tx_data_subpacket, sizeof(BYTE), zm-&gt;block_size, fp);

		if (zm-&gt;progress != NULL)
			zm-&gt;progress(zm-&gt;cbdata, ftello(fp));

		tx_type = ZCRCW;

		/** ZMODEM.DOC:
			ZCRCW data subpackets expect a response before the next frame is sent.
			If the receiver does not indicate overlapped I/O capability with the
			CANOVIO bit, or sets a buffer size, the sender uses the ZCRCW to allow
			the receiver to write its buffer before sending more data.
		***/
		/* Note: we always use ZCRCW for the first frame */
		if (subpkts_sent || len &lt; zm-&gt;block_size) {
			/*  ZMODEM.DOC:
				In the absence of fatal error, the sender eventually encounters end of
				file.  If the end of file is encountered within a frame, the frame is
				closed with a ZCRCE data subpacket which does not elicit a response
				except in case of error.
			*/
			if (len &lt; zm-&gt;block_size || zm-&gt;consecutive_errors)
				tx_type = ZCRCE;
			else {
				if (zm-&gt;can_overlap_io &amp;&amp; !zm-&gt;no_streaming &amp;&amp; (zm-&gt;recv_bufsize == 0 || buf_sent + len &lt; zm-&gt;recv_bufsize)) {
					if (zm-&gt;can_full_duplex &amp;&amp; zm-&gt;max_window_size)
						tx_type = (subpkts_sent % (zm-&gt;max_window_size / zm-&gt;block_size / 4)) == 0 ? ZCRCQ : ZCRCG;
					else
						tx_type = ZCRCG;
				}
				else    /* Send a ZCRCW frame */
					buf_sent = 0;
			}
		}

		lprintf(zm, LOG_DEBUG, "%lu Sending %s data subpacket (%lu bytes) window: %lu / %lu"
		        , (ulong)pos, chr(tx_type), len, (ulong)zm-&gt;current_window_size, (ulong)zm-&gt;max_window_size);
		if (zmodem_send_data(zm, tx_type, zm-&gt;tx_data_subpacket, len) != SEND_SUCCESS) {
			zm-&gt;consecutive_errors++;
			continue;
		}</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">
		zm-&gt;current_window_size += len;
		zm-&gt;current_file_pos += len;
		if (zm-&gt;current_file_pos &gt; zm-&gt;current_file_size)
			zm-&gt;current_file_size = zm-&gt;current_file_pos;
		subpkts_sent++;

		if (zmodem_end_of_frame(tx_type)) {
			lprintf(zm, LOG_DEBUG, "%lu Sent end-of-frame (%s subpacket)", (ulong)pos, chr(tx_type));
			if (tx_type == ZCRCW) {  /* ZACK expected */
				lprintf(zm, LOG_DEBUG, "%lu Waiting for ZACK", (ulong)pos);
				while (is_connected(zm)) {
					int ack;
					if ((ack = zmodem_recv_header(zm)) != ZACK)
						return ack;

					if (is_cancelled(zm))
						return ZCAN;

					if (zmodem_handle_zack(zm, (uint32_t)zm-&gt;current_file_pos, (uint32_t)zm-&gt;current_file_pos)) {
						zm-&gt;current_window_size = 0;
						break;
					}
				}
			}
		}

		if (sent != NULL)
			*sent += len;

		buf_sent += len;

		if (len &lt; zm-&gt;block_size) {
			lprintf(zm, LOG_DEBUG, "%lu End of file (or read error) reached", (ulong)zm-&gt;current_file_pos);
			zmodem_send_zeof(zm);
			return zmodem_recv_header(zm);  /* If this is ZRINIT, Success */
		}
		backchannel_wait = 0;

		zm-&gt;consecutive_errors = 0;

		if (zm-&gt;block_size &lt; zm-&gt;max_block_size) {
			zm-&gt;block_size *= 2;
			if (zm-&gt;block_size &gt; zm-&gt;max_block_size)
				zm-&gt;block_size = zm-&gt;max_block_size;
		}
	}

	lprintf(zm, LOG_WARNING, "%s Returning unexpectedly!", __FUNCTION__);

	/*
	 * end of file reached.
	 * should receive something... so fake ZACK
	 */

	return ZACK;
}

/*
 * send a file; returns true when session is successful. (or file is skipped)
 */

BOOL zmodem_send_file(zmodem_t* zm, char* fname, FILE* fp, BOOL request_init, time_t* start, uint64_t* sent)
{
	uint64_t        pos = 0;
	uint64_t        sent_bytes;
	struct stat     s;
	unsigned char * p;
	uchar           zfile_frame[] = { ZFILE, 0, 0, 0, 0 };
	int             type;</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">	int             i;
	unsigned        attempts;

	if (zm-&gt;block_size == 0)
		zm-&gt;block_size = ZBLOCKLEN;

	if (zm-&gt;block_size &lt; 128)
		zm-&gt;block_size = 128;

	if (zm-&gt;block_size &gt; sizeof(zm-&gt;tx_data_subpacket))
		zm-&gt;block_size = sizeof(zm-&gt;tx_data_subpacket);

	if (zm-&gt;max_block_size &lt; zm-&gt;block_size)
		zm-&gt;max_block_size = zm-&gt;block_size;

	if (zm-&gt;max_block_size &gt; sizeof(zm-&gt;rx_data_subpacket))
		zm-&gt;max_block_size = sizeof(zm-&gt;rx_data_subpacket);

	if (sent != NULL)
		*sent = 0;

	if (start != NULL)
		*start = time(NULL);

	zm-&gt;file_skipped = FALSE;

	if (zm-&gt;no_streaming)
		lprintf(zm, LOG_WARNING, "Streaming disabled");

	if (request_init) {
		for (zm-&gt;errors = 0; zm-&gt;errors &lt;= zm-&gt;max_errors &amp;&amp; !is_cancelled(zm) &amp;&amp; is_connected(zm); zm-&gt;errors++) {
			if (zm-&gt;errors)
				lprintf(zm, LOG_NOTICE, "Sending ZRQINIT (%u of %u)"
				        , zm-&gt;errors + 1, zm-&gt;max_errors + 1);
			else
				lprintf(zm, LOG_INFO, "Sending ZRQINIT");
			i = zmodem_get_zrinit(zm);
			if (i == ZRINIT)
				break;
			lprintf(zm, LOG_WARNING, "%s UNEXPECTED %s received instead of ZRINIT"
			        , __FUNCTION__, frame_desc(i));
		}
		if (zm-&gt;errors &gt;= zm-&gt;max_errors || is_cancelled(zm) || !is_connected(zm))
			return FALSE;
	}

	fstat(fileno(fp), &amp;s);
	zm-&gt;current_file_size = s.st_size;
	SAFECOPY(zm-&gt;current_file_name, getfname(fname));

	/*
	 * the file exists. now build the ZFILE frame
	 */

	/*
	 * set conversion option
	 * (not used; always binary)
	 */

	zfile_frame[ZF0] = ZF0_ZCBIN;

	/*
	 * management option
	 */

	if (zm-&gt;management_protect) {
		zfile_frame[ZF1] = ZF1_ZMPROT;
		lprintf(zm, LOG_DEBUG, "protecting destination");
	}
	else if (zm-&gt;management_clobber) {</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">		zfile_frame[ZF1] = ZF1_ZMCLOB;
		lprintf(zm, LOG_DEBUG, "overwriting destination");
	}
	else if (zm-&gt;management_newer) {
		zfile_frame[ZF1] = ZF1_ZMNEW;
		lprintf(zm, LOG_DEBUG, "overwriting destination if newer");
	}
	else
		zfile_frame[ZF1] = ZF1_ZMCRC;

	/*
	 * transport options
	 * (just plain normal transfer)
	 */

	zfile_frame[ZF2] = ZF2_ZTNOR;

	/*
	 * extended options
	 */

	zfile_frame[ZF3] = 0;

	/*
	 * now build the data subpacket with the file name and lots of other
	 * useful information.
	 */

	/*
	 * first enter the name and a 0
	 */

	p = zm-&gt;tx_data_subpacket;

	strncpy((char *)zm-&gt;tx_data_subpacket, getfname(fname), sizeof(zm-&gt;tx_data_subpacket) - 1);
	zm-&gt;tx_data_subpacket[sizeof(zm-&gt;tx_data_subpacket) - 1] = 0;

	p += strlen((char*)p) + 1;

	sprintf((char*)p, "%" PRId64 " %" PRIoMAX " 0 0 %u %" PRId64 " 0"
	        , zm-&gt;current_file_size /* use for estimating only, could be zero! */
	        , (uintmax_t)s.st_mtime
	        , zm-&gt;files_remaining
	        , zm-&gt;bytes_remaining
	        );

	p += strlen((char*)p) + 1;

	for (type = INVALIDSUBPKT, attempts = 0; type != ZRPOS; attempts++) {

		if (attempts &gt;= zm-&gt;max_errors)
			return FALSE;

		/*
		 * send the header and the data
		 */

		lprintf(zm, LOG_DEBUG, "Sending ZFILE frame: '%s'"
		        , zm-&gt;tx_data_subpacket + strlen((char*)zm-&gt;tx_data_subpacket) + 1);

		if ((i = zmodem_send_bin_header(zm, zfile_frame)) != SEND_SUCCESS) {
			lprintf(zm, LOG_DEBUG, "zmodem_send_bin_header returned %d", i);
			continue;
		}
		if ((i = zmodem_send_data_subpkt(zm, ZCRCW, zm-&gt;tx_data_subpacket, p - zm-&gt;tx_data_subpacket)) != SEND_SUCCESS) {
			lprintf(zm, LOG_DEBUG, "zmodem_send_data_subpkt returned %d", i);
			continue;
		}
		/*
		 * wait for anything but an ZACK packet</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">		 */

		do {
			type = zmodem_recv_header(zm);
			if (is_cancelled(zm))
				return FALSE;
		} while (type == ZACK &amp;&amp; is_connected(zm));

		if (!is_connected(zm))
			return FALSE;

#if 0
		lprintf(zm, LOG_INFO, "type : %d", type);
#endif

		if (type == ZCRC) {
			if (zm-&gt;crc_request == 0)
				lprintf(zm, LOG_NOTICE, "Receiver requested CRC of entire file");
			else
				lprintf(zm, LOG_NOTICE, "Receiver requested CRC of first %u bytes of file"
				        , zm-&gt;crc_request);
			zmodem_send_pos_header(zm, ZCRC, fcrc32(fp, zm-&gt;crc_request), /* Hex: */ TRUE);
			type = zmodem_recv_header(zm);
		}

		if (type == ZSKIP) {
			zm-&gt;file_skipped = TRUE;
			lprintf(zm, LOG_WARNING, "File skipped by receiver");
			return TRUE;
		}
	}

	if (!zmodem_handle_zrpos(zm, &amp;pos))
		return FALSE;

	zm-&gt;transfer_start_pos = pos;
	zm-&gt;transfer_start_time = time(NULL);

	if (start != NULL)
		*start = zm-&gt;transfer_start_time;

	rewind(fp);
	zm-&gt;errors = 0;
	zm-&gt;consecutive_errors = 0;

	lprintf(zm, LOG_DEBUG, "%lu Sending %s", (ulong)pos, fname);
	do {
		/*
		 * and start sending
		 */

		type = zmodem_send_from(zm, fp, pos, &amp;sent_bytes);

		if (!is_connected(zm))
			return FALSE;

		if (type == ZFERR || type == ZABORT || is_cancelled(zm)) {
			lprintf(zm, LOG_WARNING, "Aborting receive");
			break;
		}

		if (type == ZSKIP) {
			zm-&gt;file_skipped = TRUE;
			lprintf(zm, LOG_WARNING, "File skipped by receiver at offset: %" PRIu64, pos + sent_bytes);
			/* ZOC sends a ZRINIT after mid-file ZSKIP, so consume the ZRINIT here */
			zmodem_recv_header(zm);
			return TRUE;
		}

		if (sent != NULL)</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">			*sent += sent_bytes;

		if (type == ZRINIT)
			return TRUE;  /* Success */

		pos = zm-&gt;ack_file_pos;

		if (type == ZACK &amp;&amp; zmodem_handle_zack(zm, (uint32_t)pos, (uint32_t)zm-&gt;current_file_pos)) {
			continue;
		}

		/* Error of some kind */

		zm-&gt;errors++;
		lprintf(zm, LOG_ERR, "%lu ERROR #%d: %s", (ulong)zm-&gt;current_file_pos, zm-&gt;errors, chr(type));

		if (zm-&gt;block_size == zm-&gt;max_block_size &amp;&amp; zm-&gt;max_block_size &gt; ZBLOCKLEN)
			zm-&gt;max_block_size /= 2;

		if (zm-&gt;block_size &gt; 128)
			zm-&gt;block_size /= 2;

		if (++zm-&gt;consecutive_errors &gt; zm-&gt;max_errors) {
			lprintf(zm, LOG_WARNING, "Too many consecutive errors: %u (%u total)"
			        , zm-&gt;consecutive_errors, zm-&gt;errors);
			break;  /* failure */
		}

		if (type == ZRPOS) {
			if (!zmodem_handle_zrpos(zm, &amp;pos))
				break;
		}
	} while (TRUE);

	lprintf(zm, LOG_WARNING, "Transfer failed on receipt of: %s", chr(type));

	return FALSE;
}

/* Returns number of successfully-received files */
int zmodem_recv_files(zmodem_t* zm, const char* download_dir, uint64_t* bytes_received)
{
	char     fpath[MAX_PATH * 2 + 2];
	FILE*    fp;
	int64_t  l;
	BOOL     skip;
	BOOL     loop;
	uint64_t b;
	uint32_t crc;
	uint32_t rcrc;
	int64_t  bytes;
	int64_t  kbytes;
	int64_t  start_bytes;
	unsigned files_received = 0;
	time_t   t;
	unsigned cps;
	unsigned timeout;
	unsigned errors;

	if (bytes_received != NULL)
		*bytes_received = 0;
	zm-&gt;current_file_num = 1;
	while (zmodem_recv_init(zm) == ZFILE) {
		bytes = zm-&gt;current_file_size;
		kbytes = bytes / 1024;
		if (kbytes &lt; 1)
			kbytes = 0;
		lprintf(zm, LOG_INFO, "Downloading %s (%" PRId64 " KBytes) via ZMODEM", zm-&gt;current_file_name, kbytes);

		do {    /* try */</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">			skip = TRUE;
			loop = FALSE;

			SAFEPRINTF2(fpath, "%s/%s", download_dir, zm-&gt;current_file_name);
			lprintf(zm, LOG_DEBUG, "fpath=%s", fpath);
			if (fexist(fpath)) {
				l = flength(fpath);
				lprintf(zm, LOG_WARNING, "%s already exists (%" PRId64 " bytes)", fpath, l);
				if (l &gt;= (int32_t)bytes) {
					lprintf(zm, LOG_WARNING, "Local file size &gt;= remote file size (%" PRId64 ")"
					        , bytes);
					if (zm-&gt;duplicate_filename == NULL)
						break;
					else {
						if (l &gt; (int32_t)bytes) {
							if (zm-&gt;duplicate_filename(zm-&gt;cbdata, zm)) {
								loop = TRUE;
								continue;
							}
							break;
						}
					}
				}
				if ((fp = fopen(fpath, "rb")) == NULL) {
					lprintf(zm, LOG_ERR, "Error %d opening %s", errno, fpath);
					break;
				}
				setvbuf(fp, NULL, _IOFBF, 0x10000);

				lprintf(zm, LOG_NOTICE, "Requesting CRC of remote file: %s", zm-&gt;current_file_name);
				if (!zmodem_request_crc(zm, (uint32_t)l)) {
					fclose(fp);
					lprintf(zm, LOG_ERR, "Failed to request CRC of remote file");
					break;
				}
				lprintf(zm, LOG_NOTICE, "Calculating CRC of: %s", fpath);
				crc = fcrc32(fp, (uint32_t)l); /* Warning: 4GB limit! */
				fclose(fp);
				lprintf(zm, LOG_INFO, "CRC of %s (%lu bytes): %08X"
				        , getfname(fpath), (ulong)l, crc);
				lprintf(zm, LOG_NOTICE, "Waiting for CRC of remote file: %s", zm-&gt;current_file_name);
				if (!zmodem_recv_crc(zm, &amp;rcrc)) {
					lprintf(zm, LOG_ERR, "Failed to get CRC of remote file");
					break;
				}
				if (crc != rcrc) {
					lprintf(zm, LOG_WARNING, "Remote file has different CRC value: %08X", rcrc);
					if (zm-&gt;duplicate_filename) {
						if (zm-&gt;duplicate_filename(zm-&gt;cbdata, zm)) {
							loop = TRUE;
							continue;
						}
					}
					break;
				}
				if (l == (int32_t)bytes) {
					lprintf(zm, LOG_INFO, "CRC, length, and filename match.");
					break;
				}
				lprintf(zm, LOG_INFO, "Resuming download of %s", fpath);
			}

			if ((fp = fopen(fpath, "ab")) == NULL) {
				lprintf(zm, LOG_ERR, "Error %d opening/creating/appending %s", errno, fpath);
				break;
			}
			start_bytes = filelength(fileno(fp));
			if (start_bytes &lt; 0) {
				fclose(fp);
				lprintf(zm, LOG_ERR, "Invalid file length %" PRId64 ": %s", start_bytes, fpath);</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">				break;
			}

			skip = FALSE;
			errors = zmodem_recv_file_data(zm, fp, start_bytes);
			if (errors)
				lprintf(zm, LOG_WARNING, "%u errors occurred while receiving file: %s", errors, fpath);
			fclose(fp);
			l = flength(fpath);
			if (errors &amp;&amp; l == 0)  {   /* aborted/failed download */
				if (remove(fpath))   /* don't save 0-byte file */
					lprintf(zm, LOG_ERR, "Error %d removing %s", errno, fpath);
				else
					lprintf(zm, LOG_INFO, "Deleted 0-byte file %s", fpath);
				return files_received;
			}
			else {
				if (l != bytes) {
					lprintf(zm, LOG_WARNING, "Incomplete download (%" PRId64 " bytes received, expected %" PRId64 ")"
					        , l, bytes);
					return files_received;
				} else {
					if ((t = time(NULL) - zm-&gt;transfer_start_time) &lt;= 0)
						t = 1;
					b = l - start_bytes;
					if ((cps = (unsigned)(b / t)) == 0)
						cps = 1;
					lprintf(zm, LOG_INFO, "Received %" PRIu64 " bytes successfully (%u CPS)", b, cps);
					files_received++;
					if (bytes_received != NULL)
						*bytes_received += b;
				}
				if (zm-&gt;current_file_time)
					setfdate(fpath, zm-&gt;current_file_time);
			}

		} while (loop);
		/* finally */

		if (skip) {
			lprintf(zm, LOG_WARNING, "Skipping file");
			zmodem_send_zskip(zm);
		}
		zm-&gt;current_file_num++;
	}
	if (zm-&gt;local_abort)
		zmodem_send_zabort(zm);

	/* wait for "over-and-out" */
	timeout = zm-&gt;recv_timeout;
	zm-&gt;recv_timeout = 2;
	if (zmodem_rx(zm) == 'O')
		zmodem_rx(zm);
	zm-&gt;recv_timeout = timeout;

	return files_received;
}

int zmodem_recv_init(zmodem_t* zm)
{
	int      type = CAN;
	unsigned errors;

	lprintf(zm, LOG_DEBUG, __FUNCTION__);

#if 0
	while (is_connected(zm) &amp;&amp; !is_cancelled(zm) &amp;&amp; (ch = zm-&gt;recv_byte(zm, 0)) != NOINP)
		lprintf(zm, LOG_DEBUG, __FUNCTION__ " Throwing out received: %s", chr((uchar)ch));
#endif
</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">	for (errors = 0; errors &lt;= zm-&gt;max_errors &amp;&amp; !is_cancelled(zm) &amp;&amp; is_connected(zm); errors++) {
		if (errors)
			lprintf(zm, LOG_NOTICE, "Sending ZRINIT (%u of %u)"
			        , errors + 1, zm-&gt;max_errors + 1);
		else
			lprintf(zm, LOG_INFO, "Sending ZRINIT");
		zmodem_send_zrinit(zm);

		type = zmodem_recv_header(zm);

		if (zm-&gt;local_abort)
			break;

		if (type == TIMEOUT)
			continue;

		lprintf(zm, LOG_DEBUG, "%s received %s", __FUNCTION__, chr(type));

		if (type == ZFILE) {
			zmodem_parse_zfile_subpacket(zm);
			return type;
		}

		if (type == ZFIN) {
			zmodem_send_zfin(zm);   /* ACK */
			return type;
		}

		lprintf(zm, LOG_WARNING, "%s received %s instead of ZFILE or ZFIN"
		        , __FUNCTION__, frame_desc(type));
		lprintf(zm, LOG_DEBUG, "ZF0=%02X ZF1=%02X ZF2=%02X ZF3=%02X"
		        , zm-&gt;rxd_header[ZF0], zm-&gt;rxd_header[ZF1], zm-&gt;rxd_header[ZF2], zm-&gt;rxd_header[ZF3]);
	}

	return type;
}

void zmodem_parse_zfile_subpacket(zmodem_t* zm)
{
	int   i;
	int   mode = 0;
	long  serial = -1L;
	ulong tmptime;

	SAFECOPY(zm-&gt;current_file_name, getfname((char*)zm-&gt;rx_data_subpacket));

	zm-&gt;current_file_size = 0;
	zm-&gt;current_file_time = 0;
	zm-&gt;files_remaining = 0;
	zm-&gt;bytes_remaining = 0;

	i = sscanf((char*)zm-&gt;rx_data_subpacket + strlen((char*)zm-&gt;rx_data_subpacket) + 1, "%" SCNd64 " %lo %o %lo %u %" SCNd64
	           , &amp;zm-&gt;current_file_size /* file size (decimal) */
	           , &amp;tmptime       /* file time (octal unix format) */
	           , &amp;mode          /* file mode */
	           , &amp;serial        /* program serial number */
	           , &amp;zm-&gt;files_remaining /* remaining files to be sent */
	           , &amp;zm-&gt;bytes_remaining /* remaining bytes to be sent */
	           );
	zm-&gt;current_file_time = tmptime;

	lprintf(zm, LOG_DEBUG, "ZMODEM file (ZFILE) data (%u fields): %s"
	        , i, zm-&gt;rx_data_subpacket + strlen((char*)zm-&gt;rx_data_subpacket) + 1);

	if (!zm-&gt;files_remaining)
		zm-&gt;files_remaining = 1;
	if (!zm-&gt;bytes_remaining)
		zm-&gt;bytes_remaining = zm-&gt;current_file_size;

	if (!zm-&gt;total_files)</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">		zm-&gt;total_files = zm-&gt;files_remaining;
	if (!zm-&gt;total_bytes)
		zm-&gt;total_bytes = zm-&gt;bytes_remaining;
}

BOOL zmodem_waits_for_ack(int type)
{
	return type == ZCRCW;
}

/*
 * receive file data until the end of the file or until something goes wrong.
 * returns error count (non-zero does not mean failure).
 */

unsigned zmodem_recv_file_data(zmodem_t* zm, FILE* fp, int64_t offset)
{
	int      type = INVALIDSUBPKT;      // data subpacket type
	unsigned errors = 0;
	off_t    pos = (off_t)offset;

	zm-&gt;transfer_start_pos = offset;
	zm-&gt;transfer_start_time = time(NULL);

	if (fseeko(fp, pos, SEEK_SET) != 0) {
		lprintf(zm, LOG_ERR, "%s ERROR %d seeking to file offset %" PRId64
		        , __FUNCTION__, errno, offset);
		zmodem_send_pos_header(zm, ZFERR, (uint32_t)pos, /* Hex? */ TRUE);
		return 1; /* errors */
	}
	zmodem_send_pos_header(zm, ZRPOS, (uint32_t)pos, /* Hex? */ TRUE);

	/*  zmodem.doc:

		The zmodem receiver uses the file length [from ZFILE data] as an estimate only.
		It may be used to display an estimate of the transmission time,
		and may be compared with the amount of free disk space.  The
		actual length of the received file is determined by the data
		transfer. A file may grow after transmission commences, and
		all the data will be sent.
	*/
	while (is_connected(zm) &amp;&amp; !is_cancelled(zm)) {

		if (pos &gt; zm-&gt;current_file_size)
			zm-&gt;current_file_size = pos;

		if (zm-&gt;max_file_size != 0 &amp;&amp; pos &gt;= zm-&gt;max_file_size) {
			lprintf(zm, LOG_ERR, "%lu Specified maximum file size (%" PRId64 " bytes) reached"
			        , (ulong)pos, zm-&gt;max_file_size);
			zmodem_send_pos_header(zm, ZFERR, (uint32_t)pos, /* Hex? */ TRUE);
			++errors;
			break;
		}

		int result = zmodem_recv_file_frame(zm, fp, &amp;type);
		pos = ftello(fp);
		if (result == ENDOFFRAME) {
			lprintf(zm, LOG_DEBUG, "%lu Complete data frame received (type: %s)", (ulong)pos, chr(type));
			continue;
		}
		if (result == ZEOF || result == ZFIN) {
			lprintf(zm, LOG_INFO, "%lu Received: %s", (ulong)pos, chr(result));
			break;
		}
		errors++;
		lprintf(zm, LOG_WARNING, "%lu ERROR #%d: %s (type: %s)", (ulong)pos, errors, chr(result), chr(type));
		if (errors &gt; zm-&gt;max_errors) {
			lprintf(zm, LOG_ERR, "%lu Maximum errors (%u) exceeded", (ulong)pos, zm-&gt;max_errors);
			break;
		}</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">		if (zmodem_waits_for_ack(type))
			zmodem_recv_purge(zm, /* timeout: */ 1);
		lprintf(zm, LOG_NOTICE, "%lu Repositioning sender (sending ZRPOS)", (ulong)pos);
		zmodem_send_pos_header(zm, ZRPOS, (uint32_t)pos, /* Hex? */ TRUE);
	}

	return errors;
}


int zmodem_recv_file_frame(zmodem_t* zm, FILE* fp, int* type)
{
	int      result;
	unsigned attempt;

	/*
	 * wait for a ZDATA header with the right file offset
	 * or a timeout or a ZFIN
	 */

	for (attempt = 0;; attempt++) {
		if (attempt &gt;= zm-&gt;max_errors)
			return TIMEOUT;
		result = zmodem_recv_header(zm);
		switch (result) {
			case ZEOF:
				/* ZMODEM.DOC:
				   If the receiver has not received all the bytes of the file,
				   the receiver ignores the ZEOF because a new ZDATA is coming.
				*/
				if (zm-&gt;rxd_header_pos == (uint32_t)ftello(fp))
					return result;
				lprintf(zm, LOG_WARNING, "Ignoring ZEOF as all bytes (%u) have not been received"
				        , zm-&gt;rxd_header_pos);
				continue;
			case ZFIN:
			case TIMEOUT:
				return result;
		}
		if (is_cancelled(zm) || !is_connected(zm))
			return ZCAN;

		if (result == ZDATA)
			break;

		lprintf(zm, LOG_WARNING, "%lu Received %s instead of ZDATA frame", (ulong)ftello(fp), frame_desc(result));
	}

	if (zm-&gt;rxd_header_pos != (uint32_t)ftello(fp)) {
		lprintf(zm, LOG_WARNING, "%lu Received ZDATA frame with invalid position: %lu"
		        , (ulong)ftello(fp), (ulong)zm-&gt;rxd_header_pos);
		return FALSE;
	}

	do {
		unsigned len = 0;
		result = zmodem_recv_data(zm, zm-&gt;rx_data_subpacket, sizeof(zm-&gt;rx_data_subpacket), &amp;len, /* ack */ TRUE, type);

/*		fprintf(stderr,"packet len %d type %d\n",n,type);
*/
		if (result == ENDOFFRAME || result == FRAMEOK) {
			if (fwrite(zm-&gt;rx_data_subpacket, sizeof(uint8_t), len, fp) != len) {
				lprintf(zm, LOG_ERR, "ERROR %d writing %u bytes at file offset %" PRIu64
				        , errno, len, (uint64_t)ftello(fp));
				zmodem_send_pos_header(zm, ZFERR, (uint32_t)ftello(fp), /* Hex? */ TRUE);
				return FALSE;
			}
		}

		if (result == FRAMEOK)</code></pre></div></div><div class="gl-flex"><div class="line-numbers gl-mr-3 !gl-p-0 gl-text-transparent"></div> <div class="gl-w-full"><pre class="code highlight gl-m-0 gl-w-full !gl-overflow-visible !gl-border-none !gl-p-0 gl-leading-0"><code data-testid="content" class="line !gl-whitespace-pre-wrap gl-ml-1">			zm-&gt;block_size = len;

		if (zm-&gt;progress != NULL)
			zm-&gt;progress(zm-&gt;cbdata, ftello(fp));

		if (is_cancelled(zm))
			return ZCAN;

	} while (result == FRAMEOK);

	return result;
}

const char* zmodem_source(void)
{
	return __FILE__;
}

char* zmodem_ver(char *buf)
{
	return strcpy(buf, "2.1");
}

void zmodem_init(zmodem_t* zm, void* cbdata
                 , int (*lputs)(void*, int level, const char* str)
                 , void (*progress)(void* unused, int64_t)
                 , int (*send_byte)(void*, uchar ch, unsigned timeout /* seconds */)
                 , int (*recv_byte)(void*, unsigned timeout /* seconds */)
                 , BOOL (*is_connected)(void*)
                 , BOOL (*is_cancelled)(void*)
                 , BOOL (*data_waiting)(void*, unsigned timeout /* seconds */)
                 , void (*flush)(void*))
{
	memset(zm, 0, sizeof(zmodem_t));

	/* Use sane default values */
	zm-&gt;init_timeout = 10;        /* seconds */
	zm-&gt;send_timeout = 10;        /* seconds (reduced from 15) */
	zm-&gt;recv_timeout = 10;        /* seconds (reduced from 20) */
	zm-&gt;crc_timeout = 120;        /* seconds */
	zm-&gt;block_size = ZBLOCKLEN;
	zm-&gt;max_block_size = ZBLOCKLEN;
	zm-&gt;max_errors = 9;
	zm-&gt;can_full_duplex = TRUE;

	zm-&gt;cbdata = cbdata;
	zm-&gt;lputs = lputs;
	zm-&gt;progress = progress;
	zm-&gt;send_byte = send_byte;
	zm-&gt;recv_byte = recv_byte;
	zm-&gt;is_connected = is_connected;
	zm-&gt;is_cancelled = is_cancelled;
	zm-&gt;data_waiting = data_waiting;
	zm-&gt;flush = flush;
}
</code></pre></div></div></div></div> <!----></div> <!----></div>
</div>

</div>
</div>
</div>

</main>
</div>


</div>
</div>


<script>
//<![CDATA[
if ('loading' in HTMLImageElement.prototype) {
  document.querySelectorAll('img.lazy').forEach(img => {
    img.loading = 'lazy';
    let imgUrl = img.dataset.src;
    // Only adding width + height for avatars for now
    if (imgUrl.indexOf('/avatar/') > -1 && imgUrl.indexOf('?') === -1) {
      const targetWidth = img.getAttribute('width') || img.width;
      imgUrl += `?width=${targetWidth}`;
    }
    img.src = imgUrl;
    img.removeAttribute('data-src');
    img.classList.remove('lazy');
    img.classList.add('js-lazy-loaded');
    img.dataset.testid = 'js-lazy-loaded-content';
  });
}

//]]>
</script>
<script>
//<![CDATA[
gl = window.gl || {};
gl.experiments = {};


//]]>
</script>




<div><!----></div><div></div></body></html>