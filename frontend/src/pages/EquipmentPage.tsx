import { useEffect, useState, type FormEvent } from "react";
import { CalendarDays, MapPin, Plus, Search, Tractor, UserRound } from "lucide-react";
import { ApiError, del, get, patch, post, saveRentalToken } from "../services/api";
import type { Booking, Equipment } from "../types";
import { Alert, Button, Card, EmptyState, Field, PageHeader } from "../components/ui";

interface RentalUser {
  id: number;
  username: string;
  role: "farmer" | "owner";
  full_name?: string;
  [key: string]: unknown;
}

interface RentalSession {
  user: RentalUser;
  access_token?: string;
}

interface MachinesResponse {
  machines: Equipment[];
  types: string[];
}

interface BookingResponse {
  bookings: Booking[];
}

const emptyListing = {
  name: "",
  machine_type: "",
  hourly_rate: "",
  daily_rate: "",
  location: "",
  description: "",
};

function machineName(machine: Equipment): string {
  return machine.name ?? machine.equipment_name ?? machine.machine_name ?? "Farm equipment";
}

function dailyRate(machine: Equipment): number | undefined {
  const value = machine.daily_rate ?? machine.price_per_day ?? machine.rate_per_day;
  return typeof value === "number" ? value : undefined;
}

function displayDate(value?: string): string {
  if (!value) return "—";
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString();
}

export default function EquipmentPage() {
  const [machines, setMachines] = useState<Equipment[]>([]);
  const [types, setTypes] = useState<string[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [user, setUser] = useState<RentalUser | null>(null);
  const [mode, setMode] = useState<"browse" | "account" | "listings" | "bookings">("browse");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authRole, setAuthRole] = useState<"farmer" | "owner">("farmer");
  const [authForm, setAuthForm] = useState({ username: "", password: "", full_name: "", phone: "", location: "" });
  const [listing, setListing] = useState(emptyListing);
  const [editId, setEditId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [location, setLocation] = useState("");
  const [machineType, setMachineType] = useState("Any");
  const [bookingDates, setBookingDates] = useState<Record<number, { start_date: string; end_date: string }>>({});
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);

  async function loadMachines() {
    const params = new URLSearchParams();
    if (location.trim()) params.set("location", location.trim());
    if (machineType !== "Any") params.set("machine_type", machineType);
    const data = await get<MachinesResponse>(`/api/rental/machines${params.size ? `?${params.toString()}` : ""}`);
    setMachines(data.machines);
    setTypes(data.types);
  }

  async function loadBookings() {
    const data = await get<BookingResponse>("/api/rental/bookings", undefined, true);
    setBookings(data.bookings);
  }

  useEffect(() => {
    loadMachines().catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Equipment listings could not be loaded."));
    get<RentalSession>("/api/rental/auth/me", undefined, true)
      .then((session) => setUser(session.user))
      .catch((cause: unknown) => {
        if (cause instanceof ApiError && cause.status === 401) {
          saveRentalToken(null);
          setUser(null);
        } else {
          setError(cause instanceof Error ? cause.message : "Rental account status could not be checked.");
        }
      });
  }, []);

  useEffect(() => {
    if (!user) return;
    loadBookings().catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Bookings could not be loaded."));
  }, [user]);

  async function submitAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    setAuthLoading(true);
    try {
      const endpoint = authMode === "login" ? "/api/rental/auth/login" : "/api/rental/auth/register";
      const payload = authMode === "login"
        ? { username: authForm.username, password: authForm.password }
        : { ...authForm, role: authRole };
      const session = await post<RentalSession>(endpoint, payload);
      if (!session.access_token) throw new Error("The rental service did not return an access token.");
      saveRentalToken(session.access_token);
      setUser(session.user);
      setNotice(`Signed in as ${session.user.role}.`);
      setMode("browse");
      setAuthForm({ username: "", password: "", full_name: "", phone: "", location: "" });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not authenticate with the rental service.");
    } finally {
      setAuthLoading(false);
    }
  }

  async function submitListing(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!listing.name.trim() || !listing.machine_type || !listing.location.trim() || Number(listing.daily_rate) <= 0 || Number(listing.hourly_rate) <= 0) {
      setError("Provide a name, equipment type, location and positive hourly and daily rates.");
      return;
    }
    setError("");
    setNotice("");
    setLoading(true);
    try {
      const payload = {
        ...listing,
        hourly_rate: Number(listing.hourly_rate),
        daily_rate: Number(listing.daily_rate),
      };
      if (editId) await patch(`/api/rental/machines/${editId}`, payload, true);
      else await post("/api/rental/machines", payload, true);
      setNotice(editId ? "Equipment listing updated." : "Equipment listing added.");
      setListing(emptyListing);
      setEditId(null);
      await loadMachines();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Equipment listing could not be saved.");
    } finally {
      setLoading(false);
    }
  }

  async function deleteListing(id: number) {
    if (!window.confirm("Delete this equipment listing? Associated bookings may be removed.")) return;
    setError("");
    setNotice("");
    try {
      await del(`/api/rental/machines/${id}`, true);
      setMachines((current) => current.filter((machine) => machine.id !== id));
      setNotice("Equipment listing deleted.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "This listing could not be deleted.");
    }
  }

  async function book(machine: Equipment) {
    const dates = bookingDates[machine.id];
    if (!dates?.start_date || !dates.end_date) {
      setError("Choose both a start date and an end date before booking.");
      return;
    }
    setError("");
    setNotice("");
    try {
      const result = await post<{ ok: boolean; error?: string | null; total_cost?: number; days?: number }>(
        `/api/rental/machines/${machine.id}/bookings`,
        dates,
        true,
      );
      if (!result.ok) throw new Error(result.error || "The booking could not be created.");
      setNotice(`Booking confirmed for ${result.days} day(s) · ₹${result.total_cost?.toLocaleString("en-IN") ?? "—"}.`);
      await loadBookings();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "This equipment could not be booked.");
    }
  }

  async function cancelBooking(id: number) {
    setError("");
    setNotice("");
    try {
      await del(`/api/rental/bookings/${id}`, true);
      await loadBookings();
      setNotice("Booking cancelled.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Booking could not be cancelled.");
    }
  }

  function startEdit(machine: Equipment) {
    setEditId(machine.id);
    setListing({
      name: machineName(machine),
      machine_type: String(machine.machine_type ?? ""),
      hourly_rate: String(machine.hourly_rate ?? ""),
      daily_rate: String(machine.daily_rate ?? ""),
      location: String(machine.location ?? ""),
      description: String(machine.description ?? ""),
    });
    setMode("listings");
    setError("");
    setNotice("");
  }

  function logout() {
    saveRentalToken(null);
    setUser(null);
    setBookings([]);
    setMode("browse");
    setNotice("You have been signed out.");
  }

  const shownMachines = machines.filter((machine) =>
    `${machineName(machine)} ${machine.machine_type ?? ""} ${machine.location ?? ""}`.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <>
      <PageHeader
        eyebrow="Marketplace · Equipment access"
        title="Equipment rental"
        description="Browse local listings, manage your equipment, and book available farm machines."
        action={user ? <Button variant="secondary" onClick={logout}><UserRound size={14} /> Sign out · {user.role}</Button> : <Button variant="secondary" onClick={() => setMode("account")}><UserRound size={14} /> Farmer / owner sign in</Button>}
      />
      <div className="rental-status-strip">
        <span><span className={`service-indicator${user ? " is-connected" : ""}`} /> {user ? `${user.full_name || user.username} · ${user.role}` : "Browse listings without signing in"}</span>
        <div className="tabs">
          <button className={`tab${mode === "browse" ? " active" : ""}`} onClick={() => setMode("browse")}>Browse equipment</button>
          {user?.role === "owner" ? <button className={`tab${mode === "listings" ? " active" : ""}`} onClick={() => setMode("listings")}>Owner listings</button> : null}
          {user ? <button className={`tab${mode === "bookings" ? " active" : ""}`} onClick={() => setMode("bookings")}>My bookings</button> : null}
          {!user ? <button className={`tab${mode === "account" ? " active" : ""}`} onClick={() => setMode("account")}>Sign in / register</button> : null}
        </div>
      </div>
      {error ? <Alert tone="error">{error}</Alert> : null}
      {notice ? <Alert tone="success">{notice}</Alert> : null}

      {mode === "account" ? (
        <div className="account-layout">
          <Card>
            <div className="card-title"><div><h2>{authMode === "login" ? "Welcome back" : "Create a rental account"}</h2><p>Use your AgriVision equipment marketplace account.</p></div><span className="feature-icon"><UserRound size={16} /></span></div>
            <div className="tabs auth-tabs">
              <button className={`tab${authMode === "login" ? " active" : ""}`} onClick={() => setAuthMode("login")}>Sign in</button>
              <button className={`tab${authMode === "register" ? " active" : ""}`} onClick={() => setAuthMode("register")}>Create account</button>
            </div>
            <form className="form-stack account-form" onSubmit={submitAuth}>
              {authMode === "register" ? <>
                <Field label="Account type" id="rental-role"><select className="field" id="rental-role" value={authRole} onChange={(event) => setAuthRole(event.target.value as "farmer" | "owner")}><option value="farmer">Farmer — rent equipment</option><option value="owner">Owner — list equipment</option></select></Field>
                <Field label="Full name" id="rental-full-name"><input className="field" id="rental-full-name" value={authForm.full_name} onChange={(event) => setAuthForm({ ...authForm, full_name: event.target.value })} maxLength={160} /></Field>
              </> : null}
              <Field label="Username" id="rental-username"><input className="field" id="rental-username" value={authForm.username} onChange={(event) => setAuthForm({ ...authForm, username: event.target.value })} minLength={3} maxLength={80} required autoComplete="username" /></Field>
              <Field label="Password" id="rental-password"><input className="field" type="password" id="rental-password" value={authForm.password} onChange={(event) => setAuthForm({ ...authForm, password: event.target.value })} minLength={authMode === "register" ? 6 : 1} maxLength={256} required autoComplete={authMode === "register" ? "new-password" : "current-password"} /></Field>
              {authMode === "register" ? <>
                <Field label="Phone (optional)" id="rental-phone"><input className="field" id="rental-phone" value={authForm.phone} onChange={(event) => setAuthForm({ ...authForm, phone: event.target.value })} maxLength={40} /></Field>
                <Field label="Location (optional)" id="rental-location"><input className="field" id="rental-location" value={authForm.location} onChange={(event) => setAuthForm({ ...authForm, location: event.target.value })} maxLength={160} /></Field>
              </> : null}
              <Button type="submit" loading={authLoading}>{authMode === "login" ? "Sign in" : "Create account"}</Button>
            </form>
            <p className="home-footnote">Passwords are handled by the existing backend rental authentication; access tokens stay in this browser session.</p>
          </Card>
        </div>
      ) : null}

      {mode === "browse" ? (
        <>
          <Card className="equipment-filters">
            <div className="equipment-filter-row">
              <div className="search-wrap"><Search size={14} /><input className="field" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search equipment or location" /></div>
              <input className="field" value={location} onChange={(event) => setLocation(event.target.value)} placeholder="Filter by location" aria-label="Filter by location" />
              <select className="field" value={machineType} onChange={(event) => setMachineType(event.target.value)} aria-label="Filter by equipment type"><option>Any</option>{types.map((type) => <option key={type}>{type}</option>)}</select>
              <Button variant="secondary" onClick={() => loadMachines().catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Could not filter equipment."))}><Search size={14} /> Apply filters</Button>
            </div>
          </Card>
          {shownMachines.length ? (
            <div className="equipment-grid">
              {shownMachines.map((machine) => {
                const available = Boolean(machine.available);
                const dates = bookingDates[machine.id] ?? { start_date: "", end_date: "" };
                const ownedByUser = user?.role === "owner" && Number(machine.owner_id) === user.id;
                return (
                  <Card className="equipment-card" key={machine.id}>
                    <div className="equipment-card-head"><span className="feature-icon"><Tractor size={17} /></span><span className={`status-pill ${available ? "" : "status-offline"}`}>{available ? "Available" : "Unavailable"}</span></div>
                    <h3>{machineName(machine)}</h3>
                    <div className="tag-row"><span className="tag">{machine.machine_type ?? "Equipment"}</span>{machine.location ? <span className="tag"><MapPin size={10} /> {machine.location}</span> : null}</div>
                    {machine.description ? <p>{machine.description}</p> : null}
                    <div className="equipment-rate"><strong>₹{dailyRate(machine)?.toLocaleString("en-IN") ?? "—"}</strong><span>/ day</span>{machine.hourly_rate ? <span className="equipment-hourly">₹{String(machine.hourly_rate)}/hr</span> : null}</div>
                    {ownedByUser ? <div className="form-actions"><Button className="button-small" variant="secondary" onClick={() => startEdit(machine)}>Edit listing</Button><Button className="button-small danger-button" variant="secondary" onClick={() => deleteListing(machine.id)}>Delete</Button></div> : user?.role === "farmer" && available ? (
                      <div className="booking-inline">
                        <input className="field" type="date" aria-label={`Booking start for ${machineName(machine)}`} value={dates.start_date} onChange={(event) => setBookingDates({ ...bookingDates, [machine.id]: { ...dates, start_date: event.target.value } })} />
                        <input className="field" type="date" aria-label={`Booking end for ${machineName(machine)}`} value={dates.end_date} onChange={(event) => setBookingDates({ ...bookingDates, [machine.id]: { ...dates, end_date: event.target.value } })} />
                        <Button className="button-small" onClick={() => book(machine)}><CalendarDays size={13} /> Book</Button>
                      </div>
                    ) : !user ? <Button className="button-small equipment-cta" variant="soft" onClick={() => setMode("account")}>Sign in to book <UserRound size={13} /></Button> : null}
                  </Card>
                );
              })}
            </div>
          ) : <Card><EmptyState icon={<Tractor size={23} />}>No equipment matches those filters. Try another location or equipment type.</EmptyState></Card>}
        </>
      ) : null}

      {mode === "listings" && user?.role === "owner" ? (
        <div className="owner-layout">
          <Card>
            <div className="card-title"><div><h2>{editId ? "Edit equipment listing" : "Add equipment listing"}</h2><p>Provide accurate rates and availability details.</p></div><span className="feature-icon"><Plus size={16} /></span></div>
            <form className="form-stack" onSubmit={submitListing}>
              <Field label="Equipment name" id="listing-name"><input className="field" id="listing-name" value={listing.name} onChange={(event) => setListing({ ...listing, name: event.target.value })} maxLength={160} required /></Field>
              <Field label="Type" id="listing-type"><select className="field" id="listing-type" value={listing.machine_type} onChange={(event) => setListing({ ...listing, machine_type: event.target.value })} required><option value="">Choose type</option>{types.map((type) => <option key={type}>{type}</option>)}</select></Field>
              <div className="field-grid">
                <Field label="Hourly rate (₹)" id="listing-hourly"><input className="field" id="listing-hourly" type="number" min="0.01" step="any" value={listing.hourly_rate} onChange={(event) => setListing({ ...listing, hourly_rate: event.target.value })} required /></Field>
                <Field label="Daily rate (₹)" id="listing-daily"><input className="field" id="listing-daily" type="number" min="0.01" step="any" value={listing.daily_rate} onChange={(event) => setListing({ ...listing, daily_rate: event.target.value })} required /></Field>
              </div>
              <Field label="Location" id="listing-location"><input className="field" id="listing-location" value={listing.location} onChange={(event) => setListing({ ...listing, location: event.target.value })} maxLength={160} required /></Field>
              <Field label="Description (optional)" id="listing-description"><textarea className="field" id="listing-description" value={listing.description} onChange={(event) => setListing({ ...listing, description: event.target.value })} maxLength={2000} /></Field>
              <div className="form-actions"><Button type="submit" loading={loading}>{editId ? "Save changes" : "Add listing"}</Button>{editId ? <Button type="button" variant="secondary" onClick={() => { setEditId(null); setListing(emptyListing); }}>Cancel edit</Button> : null}</div>
            </form>
          </Card>
          <div>
            <div className="section-row"><h2>Your equipment</h2><span>{machines.filter((machine) => Number(machine.owner_id) === user.id).length} listings</span></div>
            {machines.filter((machine) => Number(machine.owner_id) === user.id).length ? machines.filter((machine) => Number(machine.owner_id) === user.id).map((machine) => (
              <Card className="owner-listing" key={machine.id}><div><strong>{machineName(machine)}</strong><span>{String(machine.machine_type ?? "Equipment")} · {String(machine.location ?? "")}</span></div><div className="form-actions"><Button className="button-small" variant="secondary" onClick={() => startEdit(machine)}>Edit</Button><Button className="button-small danger-button" variant="secondary" onClick={() => deleteListing(machine.id)}>Delete</Button></div></Card>
            )) : <Card><EmptyState icon={<Plus size={21} />}>Add your first equipment listing using the form.</EmptyState></Card>}
          </div>
        </div>
      ) : null}

      {mode === "bookings" && user ? (
        <Card>
          <div className="card-title"><div><h2>{user.role === "owner" ? "Bookings for your equipment" : "Your equipment bookings"}</h2><p>Rental dates, status and estimated costs.</p></div><span className="feature-icon"><CalendarDays size={16} /></span></div>
          {bookings.length ? <div className="table-wrap"><table><thead><tr><th>Equipment</th><th>Start</th><th>End</th><th>Status</th><th>Cost</th><th /></tr></thead><tbody>{bookings.map((booking) => <tr key={booking.id}><td>{booking.equipment_name ?? booking.machine_name ?? `Machine #${booking.machine_id}`}</td><td>{displayDate(booking.start_date)}</td><td>{displayDate(booking.end_date)}</td><td><span className={`status-pill ${booking.status === "cancelled" ? "status-offline" : ""}`}>{booking.status ?? "Confirmed"}</span></td><td>{typeof booking.total_cost === "number" ? `₹${booking.total_cost.toLocaleString("en-IN")}` : "—"}</td><td>{booking.status !== "cancelled" ? <Button className="button-small danger-button" variant="secondary" onClick={() => cancelBooking(booking.id)}>Cancel</Button> : null}</td></tr>)}</tbody></table></div> : <EmptyState icon={<CalendarDays size={23} />}>No bookings have been made yet.</EmptyState>}
        </Card>
      ) : null}
    </>
  );
}
