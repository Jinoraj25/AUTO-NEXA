with open('server.py', 'r', encoding='utf-8') as f:
    code = f.read()

endpoint_code = '''        if self.path == '/api/master_rules/upload':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body_bytes = self.rfile.read(content_length)
                payload = json.loads(body_bytes.decode('utf-8'))
                
                rules = payload.get('aggregateMaster', [])
                if rules:
                    target_json = os.path.join("data", "aggregate_master_rules.json")
                    os.makedirs("data", exist_ok=True)
                    with open(target_json, "w", encoding="utf-8") as out_f:
                        json.dump({"status": "success", "count": len(rules), "aggregateMaster": rules}, out_f, ensure_ascii=False, indent=2)
                    
                    # Also insert into SQLite DB table mapping_reference_master
                    s_conn = get_db_connection()
                    if s_conn:
                        try:
                            cursor = s_conn.cursor()
                            cursor.execute("DELETE FROM mapping_reference_master")
                            db_rows = []
                            for r in rules:
                                db_rows.append((r.get('aggregate',''), r.get('subAggregate',''), r.get('component',''), r.get('category','Mechanical Parts')))
                            cursor.executemany("INSERT INTO mapping_reference_master (aggregate, sub_aggregate, component, category) VALUES (?, ?, ?, ?)", db_rows)
                            s_conn.commit()
                            s_conn.close()
                            print(f"SQLite DB: Updated mapping_reference_master with {len(rules)} rules.")
                        except Exception as dbe:
                            print(f"DB master upload insert warning: {dbe}")

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "count": len(rules), "message": f"Successfully updated Aggregate Master rules in SQL DB ({len(rules)} rules)"}).encode('utf-8'))
                return
            except Exception as e:
                print(f"API Master Rules Upload Exception: {e}")
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
                return\n\n'''

# Insert before sales/commit
code_updated = code.replace("if self.path == '/api/sales/commit':", endpoint_code + "        if self.path == '/api/sales/commit':")

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(code_updated)

print("Updated server.py with /api/master_rules/upload API endpoint!")
