import { useEffect, useState } from "react";

import { api } from "../api";

import {
  BigButton,
  ErrorBanner,
  Shell,
  Spinner,
  useAction,
} from "../components/ui";

import { useApp } from "../store";

import type { ProfileResult } from "../types";


export default function HomeScreen() {
  const {
    t,
    go,
    session,
  } = useApp();

  const [
    profile,
    setProfile,
  ] = useState<ProfileResult | null>(null);

  const load = useAction(
    () => api.profile()
  );


  useEffect(() => {
    void load.run().then((result) => {
      if (result) {
        setProfile(result);
      }
    });
  }, []);


  const user =
    profile?.user ??
    session?.user;


  /*
   * Profile loading
   */
  if (load.busy && !profile) {
    return (
      <Shell
        title={
          user?.name
            ? `${t("welcome")}, ${user.name}`
            : t("welcome")
        }
        back={false}
      >
        <Spinner label={t("loading")} />
      </Shell>
    );
  }


  return (
    <Shell
      title={
        user?.name
          ? `${t("welcome")}, ${user.name}`
          : t("welcome")
      }
      back={false}
    >

      <ErrorBanner message={load.error} />


      {/* =====================================================
          PERSONAL PROFILE
      ====================================================== */}

      <section className="card profile-card">

        <h2>
          {t("profile")}
        </h2>


        <div className="profile-grid">

          {/* Name */}
          <div className="profile-item">
            <strong>
              {t("name")}
            </strong>

            <span>
              {user?.name || "Not available"}
            </span>
          </div>


          {/* Member number */}
          <div className="profile-item">
            <strong>
              {t("memberNo")}
            </strong>

            <span>
              {user?.member_no ||
                t("notAssigned")}
            </span>
          </div>


          {/* Phone */}
          <div className="profile-item">
            <strong>
              Phone number
            </strong>

            <span>
              {user?.phone ||
                "Not provided"}
            </span>
          </div>


          {/* Address */}
          <div className="profile-item profile-item-wide">
            <strong>
              Address
            </strong>

            <span>
              {user?.address ||
                "Not provided"}
            </span>
          </div>


          {/* Society */}
          <div className="profile-item">
            <strong>
              {t("members")}
            </strong>

            <span>
              {user?.society_name ||
                "Not provided"}
            </span>
          </div>


          {/* Profession */}
          <div className="profile-item">
            <strong>
              {t("profession")}
            </strong>

            <span>
              {user?.profession ||
                "Not provided"}
            </span>
          </div>


          {/* Land ownership */}
          <div className="profile-item">
            <strong>
              {t("landOwned")}
            </strong>

            <span>

              {user?.land_owned === true
                ? "Yes"
                : user?.land_owned === false
                  ? "No"
                  : "Not provided"}

            </span>
          </div>


          {/* Land area */}
          {user?.land_owned === true && (
            <div className="profile-item">
              <strong>
                {t("landArea")}
              </strong>

              <span>
                {user.land_area ||
                  "Not provided"}
              </span>
            </div>
          )}


          {/* Registration status */}
          <div className="profile-item">

            <strong>
              Registration status
            </strong>

            <span className="status-approved">
              {user?.registration_status ===
              "approved"
                ? "Approved"
                : user?.registration_status ||
                  "Unknown"}
            </span>

          </div>

        </div>

      </section>


      {/* =====================================================
          PREVIOUS COMPLAINTS
      ====================================================== */}

      <section className="card">

        <h2>
          Previous Complaints
        </h2>


        {profile?.complaints &&
        profile.complaints.length > 0 ? (

          <div className="complaint-list">

            {profile.complaints.map(
              (complaint) => (

                <div
                  className="complaint-item"
                  key={complaint.id}
                >

                  <strong>
                    {complaint.reference}
                  </strong>

                  <div>
                    Category:{" "}
                    {complaint.category}
                  </div>

                  <div>
                    Status:{" "}
                    {complaint.status}
                  </div>

                  <div>
                    Date:{" "}
                    {complaint.created_at}
                  </div>

                  {complaint.details && (
                    <div>
                      Details:{" "}
                      {complaint.details}
                    </div>
                  )}

                </div>

              )
            )}

          </div>

        ) : (

          <div className="empty-profile-section">

            <div className="empty-icon">
              ✓
            </div>

            <strong>
              No complaints till now
            </strong>

            <p className="muted">
              You have not submitted any
              complaint through Jansaarthi yet.
            </p>

          </div>

        )}

      </section>


      {/* =====================================================
          PENDING SCHEMES
      ====================================================== */}

      <section className="card">

        <h2>
          Pending Schemes
        </h2>


        {(
          profile?.pending_schemes ??
          user?.pending_schemes ??
          []
        ).length > 0 ? (

          <div className="scheme-list">

            {(
              profile?.pending_schemes ??
              user?.pending_schemes ??
              []
            ).map(
              (scheme, index) => (

                <div
                  className="scheme-item"
                  key={`${scheme}-${index}`}
                >
                  • {scheme}
                </div>

              )
            )}

          </div>

        ) : (

          <div className="empty-profile-section">

            <div className="empty-icon">
              ✓
            </div>

            <strong>
              No pending schemes
            </strong>

            <p className="muted">
              You currently have no pending
              government schemes.
            </p>

          </div>

        )}

      </section>


      {/* =====================================================
          SCANNED DOCUMENTS
      ====================================================== */}

      <section className="card">

        <h2>
          Documents
        </h2>


        {profile?.owned_documents &&
        profile.owned_documents.length > 0 ? (

          <div className="document-list">

            {profile.owned_documents.map(
              (document) => (

                <div
                  className="document-item"
                  key={document.id}
                >
                  📄{" "}
                  <strong>
                    {document.filename}
                  </strong>

                  <span>
                    {document.created_at}
                  </span>
                </div>

              )
            )}

          </div>

        ) : (

          <div className="empty-profile-section">

            <strong>
              No documents scanned yet
            </strong>

            <p className="muted">
              Documents you scan through
              Jansaarthi will appear here.
            </p>

          </div>

        )}

      </section>


      {/* =====================================================
          MAIN SERVICES
      ====================================================== */}

      <div className="grid home-grid">

        <BigButton
          icon="🎤"
          variant="primary"
          onClick={() =>
            go({ name: "voice" })
          }
        >
          {t("askByVoice")}
        </BigButton>


        <BigButton
          icon="📄"
          variant="primary"
          onClick={() =>
            go({ name: "scan" })
          }
        >
          {t("scanDocument")}
        </BigButton>


        <BigButton
          icon="🌾"
          variant="primary"
          onClick={() =>
            go({ name: "schemes" })
          }
        >
          {t("findSchemes")}
        </BigButton>


        <BigButton
          icon="✍️"
          variant="primary"
          onClick={() =>
            go({ name: "complaint" })
          }
        >
          {t("makeComplaint")}
        </BigButton>

      </div>

    </Shell>
  );
}