import datetime
from typing import Dict, List, Optional


class HospitalAppointmentSystem:
    CONSULTATION_MINUTES = 15  # average consultation time per patient

    def __init__(self):
        # Doctor data: id -> info
        self.doctors: Dict[int, Dict] = {
            1: {"name": "Dr. Sharma", "department": "General Medicine", "token_counter": 0, "queue": []},
            2: {"name": "Dr. Rao", "department": "Pediatrics", "token_counter": 0, "queue": []},
            3: {"name": "Dr. Iyer", "department": "Orthopedics", "token_counter": 0, "queue": []},
        }

        # Token -> patient/appointment record
        self.patients: Dict[str, Dict] = {}

    # ------------- HELPER METHODS -------------

    def _generate_token(self, doctor_id: int) -> str:
        """Generate a new token number for a specific doctor."""
        doctor = self.doctors[doctor_id]
        doctor["token_counter"] += 1
        return f"D{doctor_id}-{doctor['token_counter']}"

    def _get_doctor_queue_estimates(self, doctor_id: int) -> Dict[str, datetime.datetime]:
        """
        For a given doctor, calculate estimated consultation time for each token
        based on current position in the queue.
        """
        doctor = self.doctors[doctor_id]
        queue = doctor["queue"]
        base_time = datetime.datetime.now()
        estimates: Dict[str, datetime.datetime] = {}

        for position, token in enumerate(queue):
            estimated_time = base_time + datetime.timedelta(
                minutes=position * self.CONSULTATION_MINUTES
            )
            estimates[token] = estimated_time

        return estimates

    def _next_available_time(self, doctor_id: int) -> datetime.datetime:
        """Return next available time for a doctor based on current queue."""
        doctor = self.doctors[doctor_id]
        queue_length = len(doctor["queue"])
        now = datetime.datetime.now()
        return now + datetime.timedelta(
            minutes=queue_length * self.CONSULTATION_MINUTES
        )

    # ------------- CORE FEATURES ------------

    def register_patient(
        self,
        name: str,
        age: int,
        doctor_id: int,
        emergency: bool = False,
    ) -> str:
        """
        Register a new patient:
        - Assign token (doctor-wise)
        - Add to doctor's queue (emergency patients get priority)
        - Store patient details
        """

        if doctor_id not in self.doctors:
            return "Invalid doctor ID."

        doctor = self.doctors[doctor_id]
        token = self._generate_token(doctor_id)
        registered_at = datetime.datetime.now()

        # Add token to queue (emergency -> front, normal -> end)
        if emergency:
            doctor["queue"].insert(0, token)
        else:
            doctor["queue"].append(token)

        self.patients[token] = {
            "token": token,
            "name": name,
            "age": age,
            "doctor_id": doctor_id,
            "doctor_name": doctor["name"],
            "department": doctor["department"],
            "registered_at": registered_at,
            "status": "Waiting",  # Waiting / Consulted
            "consulted_at": None,
            "emergency": emergency,
        }

        # Calculate estimated time based on current queue
        estimates = self._get_doctor_queue_estimates(doctor_id)
        estimated_time = estimates.get(token)

        emergency_tag = " (EMERGENCY)" if emergency else ""
        msg_lines = [
            "Patient Registered Successfully!",
            f"Name       : {name}",
            f"Age        : {age}",
            f"Department : {doctor['department']}",
            f"Doctor     : {doctor['name']}",
            f"Token No.  : {token}{emergency_tag}",
        ]

        if estimated_time:
            msg_lines.append(
                "Estimated Consultation Time: "
                + estimated_time.strftime("%Y-%m-%d %H:%M")
            )

        return "\n".join(msg_lines)

    def mark_consulted(self, token: str) -> str:
        """Mark a patient as consulted and remove from doctor's queue."""
        patient = self.patients.get(token)
        if not patient:
            return "Invalid token number."

        if patient["status"] == "Consulted":
            return "This patient is already marked as consulted."

        doctor_id = patient["doctor_id"]
        doctor = self.doctors[doctor_id]

        # Remove token from queue if present
        if token in doctor["queue"]:
            doctor["queue"].remove(token)

        patient["status"] = "Consulted"
        patient["consulted_at"] = datetime.datetime.now()

        return (
            f"Token {token} - {patient['name']} marked as CONSULTED "
            f"by {doctor['name']} ({doctor['department']})."
        )

    def search_by_token(self, token: str) -> str:
        """Search patient using token number."""
        patient = self.patients.get(token)
        if not patient:
            return "No patient found with this token."

        doctor_id = patient["doctor_id"]
        estimates = self._get_doctor_queue_estimates(doctor_id)
        estimated_time = estimates.get(token)

        lines = [
            "Patient Details:",
            f"Token       : {patient['token']}",
            f"Name        : {patient['name']}",
            f"Age         : {patient['age']}",
            f"Department  : {patient['department']}",
            f"Doctor      : {patient['doctor_name']}",
            f"Status      : {patient['status']}",
            f"Emergency   : {'Yes' if patient['emergency'] else 'No'}",
            "Registered  : " + patient["registered_at"].strftime("%Y-%m-%d %H:%M"),
        ]

        if patient["consulted_at"]:
            lines.append(
                "Consulted   : "
                + patient["consulted_at"].strftime("%Y-%m-%d %H:%M")
            )

        if estimated_time and patient["status"] == "Waiting":
            lines.append(
                "Estimated Consultation Time: "
                + estimated_time.strftime("%Y-%m-%d %H:%M")
            )

        return "\n".join(lines)

    def search_by_name(self, keyword: str) -> str:
        """Search patients using part of the name (case-insensitive)."""
        keyword_lower = keyword.lower()
        results: List[Dict] = [
            p for p in self.patients.values()
            if keyword_lower in p["name"].lower()
        ]

        if not results:
            return "No patients found with this name."

        lines = ["Search Results:"]
        for p in results:
            lines.append(
                f"- {p['name']} (Token: {p['token']}, Doctor: {p['doctor_name']}, "
                f"Status: {p['status']})"
            )
        return "\n".join(lines)

    def display_doctor_queues(self) -> str:
        """Display doctor-wise queues with tokens and estimated times."""
        output_lines = ["\n=== DOCTOR-WISE QUEUE DETAILS ==="]
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        output_lines.append(f"Current Time: {now_str}\n")

        for doc_id, doctor in self.doctors.items():
            output_lines.append(
                f"Doctor {doc_id}: {doctor['name']} ({doctor['department']})"
            )
            queue = doctor["queue"]

            if not queue:
                output_lines.append("  Queue: [No patients waiting]")
                next_time = self._next_available_time(doc_id)
                output_lines.append(
                    "  Next Available Time: " + next_time.strftime("%Y-%m-%d %H:%M")
                )
                output_lines.append("")
                continue

            estimates = self._get_doctor_queue_estimates(doc_id)
            output_lines.append("  Queue:")

            for position, token in enumerate(queue, start=1):
                patient = self.patients[token]
                est_time = estimates[token]
                emergency_tag = " (EMERGENCY)" if patient["emergency"] else ""
                output_lines.append(
                    f"    {position}. Token {token}{emergency_tag} - "
                    f"{patient['name']} | Est: {est_time.strftime('%H:%M')}"
                )

            next_time = self._next_available_time(doc_id)
            output_lines.append(
                "  Next Available Time: " + next_time.strftime("%Y-%m-%d %H:%M")
            )
            output_lines.append("")

        return "\n".join(output_lines)

    # ------------- PREMIUM ADD-ONS -------------

    def daily_opd_summary(self) -> str:
        """Generate a simple daily OPD summary report."""
        total_patients = len(self.patients)
        total_consulted = sum(
            1 for p in self.patients.values() if p["status"] == "Consulted"
        )
        total_waiting = total_patients - total_consulted

        lines = [
            "\n=== DAILY OPD SUMMARY REPORT ===",
            f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}",
            f"Total Patients Registered : {total_patients}",
            f"Total Consulted           : {total_consulted}",
            f"Total Waiting             : {total_waiting}",
            "",
            "Doctor-wise Patient Count:",
        ]

        for doc_id, doctor in self.doctors.items():
            count_doc = sum(
                1 for p in self.patients.values() if p["doctor_id"] == doc_id
            )
            consulted_doc = sum(
                1
                for p in self.patients.values()
                if p["doctor_id"] == doc_id and p["status"] == "Consulted"
            )
            lines.append(
                f"- {doctor['name']} ({doctor['department']}): "
                f"{count_doc} total, {consulted_doc} consulted"
            )

        # Department-wise workload analytics
        dept_counts: Dict[str, int] = {}
        for p in self.patients.values():
            dept = p["department"]
            dept_counts[dept] = dept_counts.get(dept, 0) + 1

        lines.append("\nDepartment-wise Workload:")
        for dept, count in dept_counts.items():
            lines.append(f"- {dept}: {count} patients")

        return "\n".join(lines)

    def export_to_file(self, filename: str = "hospital_opd_summary.txt") -> str:
        """
        Export patient list and daily summary to a text file.
        (Can be renamed as .pdf if required for assignment submission.)
        """
        summary = self.daily_opd_summary()

        lines = [summary, "\n\n=== PATIENT LIST ==="]
        for p in self.patients.values():
            line = (
                f"Token: {p['token']}, Name: {p['name']}, Age: {p['age']}, "
                f"Dept: {p['department']}, Doctor: {p['doctor_name']}, "
                f"Status: {p['status']}, Emergency: {'Yes' if p['emergency'] else 'No'}"
            )
            lines.append(line)

        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return f"Patient list and summary exported to {filename}"

    # ------------- MENU / UI -------------

    def run(self):
        """Main menu loop."""
        while True:
            print("\n" + "=" * 50)
            print("HOSPITAL APPOINTMENT & QUEUE MANAGEMENT SYSTEM")
            print("1. Register Patient")
            print("2. View Doctor Queues")
            print("3. Search Appointment by Token")
            print("4. Search Appointment by Patient Name")
            print("5. Mark Patient as Consulted")
            print("6. Daily OPD Summary")
            print("7. Export Patient List & Summary to File")
            print("8. Exit")

            choice = input("Enter your choice (1-8): ").strip()

            if choice == "1":
                self.menu_register_patient()
            elif choice == "2":
                print(self.display_doctor_queues())
            elif choice == "3":
                token = input("Enter Token Number: ").strip().upper()
                print(self.search_by_token(token))
            elif choice == "4":
                name = input("Enter Patient Name or part of name: ").strip()
                print(self.search_by_name(name))
            elif choice == "5":
                token = input("Enter Token Number to mark consulted: ").strip().upper()
                print(self.mark_consulted(token))
            elif choice == "6":
                print(self.daily_opd_summary())
            elif choice == "7":
                filename = input("Enter filename (default: hospital_opd_summary.txt): ").strip()
                if not filename:
                    filename = "hospital_opd_summary.txt"
                print(self.export_to_file(filename))
            elif choice == "8":
                print("Exiting Hospital Appointment System. Goodbye!")
                break
            else:
                print("Invalid choice! Please try again.")

    def menu_register_patient(self):
        """Handle patient registration input."""
        name = input("Patient Name: ").strip()
        try:
            age = int(input("Patient Age: ").strip())
        except ValueError:
            print("Invalid age entered.")
            return

        print("\nAvailable Doctors:")
        for doc_id, doc in self.doctors.items():
            print(f"{doc_id}. {doc['name']} ({doc['department']})")

        try:
            doctor_id = int(input("Select Doctor ID: ").strip())
        except ValueError:
            print("Invalid doctor ID.")
            return

        emergency_input = input("Is this an EMERGENCY case? (y/n): ").strip().lower()
        emergency = emergency_input == "y"

        result = self.register_patient(name, age, doctor_id, emergency)
        print("\n" + result)


def main():
    system = HospitalAppointmentSystem()
    system.run()


if __name__ == "__main__":
    main()

