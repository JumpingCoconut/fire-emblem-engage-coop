        add_testusers = False
        if add_testusers:
            # Quickly addding friends
            user_config = self.db.table("user_config")
            UserQ = Query()
            # JCoconut
            new_entry = {   
                            "user" : "330955309763788800",
                            "notifications_active" : True, 
                            "notifications_server_only" : False, 
                            "notifications_server_id" : "563903641631719429",
                            "notifications_group_pass" : "11118888"
                        }
            user_config.upsert(new_entry, UserQ.user == str(new_entry["user"]))
            # Deej
            new_entry = {   
                            "user" : "523211690213376005",
                            "notifications_active" : True, 
                            "notifications_server_only" : False, 
                            "notifications_server_id" : "563903641631719429",
                            "notifications_group_pass" : "11118888"
                        }
            user_config.upsert(new_entry, UserQ.user == str(new_entry["user"]))
            # NL
            new_entry = {   
                            "user" : "464342606898397186",
                            "notifications_active" : True, 
                            "notifications_server_only" : False, 
                            "notifications_server_id" : "563903641631719429",
                            "notifications_group_pass" : "11118888"
                        }
            # Valharke
            user_config.upsert(new_entry, UserQ.user == str(new_entry["user"]))
            new_entry = {   
                            "user" : "745642457101893643",
                            "notifications_active" : True, 
                            "notifications_server_only" : False, 
                            "notifications_server_id" : "563903641631719429",
                            "notifications_group_pass" : "11118888"
                        }
            # Eri
            user_config.upsert(new_entry, UserQ.user == str(new_entry["user"]))
            new_entry = {   
                            "user" : "211526001354735618",
                            "notifications_active" : True, 
                            "notifications_server_only" : False, 
                            "notifications_server_id" : "737637662764171375",
                            "notifications_group_pass" : "11118888"
                        }
            # Kambe
            user_config.upsert(new_entry, UserQ.user == str(new_entry["user"]))
            new_entry = {   
                            "user" : "535900115483885581",
                            "notifications_active" : True, 
                            "notifications_server_only" : False, 
                            "notifications_server_id" : "737637662764171375",
                            "notifications_group_pass" : "11118888"
                        }
            # Levo
            user_config.upsert(new_entry, UserQ.user == str(new_entry["user"]))
            new_entry = {   
                            "user" : "404597649585471490",
                            "notifications_active" : True, 
                            "notifications_server_only" : False, 
                            "notifications_server_id" : "563903641631719429",
                            "notifications_group_pass" : "11118888"
                        }
            user_config.upsert(new_entry, UserQ.user == str(new_entry["user"]))
            # Thaissing
            new_entry = {   
                            "user" : "210436307032342528",
                            "notifications_active" : True, 
                            "notifications_server_only" : False, 
                            "notifications_server_id" : "737637662764171375",
                            "notifications_group_pass" : "11118888"
                        }
            user_config.upsert(new_entry, UserQ.user == str(new_entry["user"]))        
            
        add_testdata = False
        if add_testdata:
            # Test data
            new_item = {    "code": "7999996", 
                            "map": 2, 
                            "server_only" : True,
                            "group_pass" : "", 
                            "status" : "open",
                            "turns" : [
                                    {
                                        "user" : str(363144319739232257),
                                        "server" : str(490564578128822293),
                                        "timestamp" : "2022-12-24T16:59:00", #datetime.datetime.utcnow().isoformat(),
                                    },
                                    {
                                        "user" : str(523211690213376005),
                                        "server" : str(490564578128822293),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                ],
                        }
            self.db.insert(new_item)
            new_item = {    "code": "663NB4R", 
                            "map": 1, 
                            "server_only" : False,
                            "group_pass" : "", 
                            "status" : "open",
                            "turns" : [
                                    {
                                        "user" : "330955309763788800", # str(ctx.user.id),
                                        "server" : "490564578128822293", #str(ctx.guild_id),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                ],
                        }
            self.db.insert(new_item) 
            new_item = {    "code": "748P526", 
                            "map": 2, 
                            "server_only" : True,
                            "group_pass" : "", 
                            "status" : "open",
                            "turns" : [
                                    {
                                        "user" : str(523211690213376005),
                                        "server" : str(490564578128822293),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                    {
                                        "user" : str(330955309763788800),
                                        "server" : str(490564578128822293),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                ],
                        }
            self.db.insert(new_item) 
            new_item = {    "code": "9996W96", 
                            "map": 3, 
                            "server_only" : False,
                            "group_pass" : "", 
                            "status" : "success",
                            "turns" : [
                                    {
                                        "user" : str(234861064532131842),
                                        "server" : str(870019135646613524),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                    {
                                        "user" : str(330955309763788800),
                                        "server" : str(870019135646613524),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                    {
                                        "user" : str(523211690213376005),
                                        "server" : str(490564578128822293),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                    {
                                        "user" : str(363144319739232257),
                                        "server" : str(870019135646613524),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                    {
                                        "user" : str(307624030704238592),
                                        "server" : str(490564578128822293),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                ],
                        }
            self.db.insert(new_item) 
            new_item = {    "code": "8896W96", 
                            "map": 4, 
                            "server_only" : False,
                            "group_pass" : "", 
                            "status" : "finished",
                            "turns" : [
                                    {
                                        "user" : str(234861064532131842),
                                        "server" : str(870019135646613524),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                    {
                                        "user" : str(330955309763788800),
                                        "server" : str(870019135646613524),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                    {
                                        "user" : str(523211690213376005),
                                        "server" : str(490564578128822293),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                ],
                        }
            self.db.insert(new_item) 
            new_item = {    "code": "9999526", 
                            "map": 5, 
                            "server_only" : False,
                            "group_pass" : "11118888", 
                            "status" : "open",
                            "turns" : [
                                    {
                                        "user" : str(330955309763788800),
                                        "server" : str(870019135646613524),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                    {
                                        "user" : str(234861064532131842),
                                        "server" : str(490564578128822293),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                    {
                                        "user" : str(363144319739232257),
                                        "server" : str(870019135646613524),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                ],
                        }
            self.db.insert(new_item) 
            new_item = {    "code": "123526", 
                            "map": 5, 
                            "server_only" : True,
                            "group_pass" : "", 
                            "status" : "open",
                            "turns" : [
                                    {
                                        "user" : str(234861064532131842),
                                        "server" : str(870019135646613524),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                    {
                                        "user" : str(307624030704238592),
                                        "server" : str(870019135646613524),
                                        "timestamp" : datetime.datetime.utcnow().isoformat(),
                                    },
                                ],
                        }
            self.db.insert(new_item) 